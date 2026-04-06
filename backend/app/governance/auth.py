# backend/app/governance/auth.py
"""
Authentication and authorization services.

Provides:
- Password hashing with bcrypt
- JWT token generation and validation
- FastAPI dependencies for auth
- Permission checking
"""

from datetime import datetime, timedelta, timezone
from typing import Annotated, Callable
from uuid import UUID

import bcrypt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.core.database import get_db_session
from backend.app.core.logging import get_logger
from backend.app.governance.models import (
    Token,
    TokenPayload,
    User,
    UserRead,
)

logger = get_logger(__name__)

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


class AuthService:
    """Service for authentication operations."""

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt.

        Args:
            password: Plain text password

        Returns:
            Hashed password string
        """
        # Encode password and generate salt
        password_bytes = password.encode("utf-8")
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode("utf-8")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.

        Args:
            plain_password: Plain text password to verify
            hashed_password: Stored hash to verify against

        Returns:
            True if password matches, False otherwise
        """
        try:
            password_bytes = plain_password.encode("utf-8")
            hashed_bytes = hashed_password.encode("utf-8")
            return bcrypt.checkpw(password_bytes, hashed_bytes)
        except Exception:
            return False

    @staticmethod
    def create_access_token(
        user: User,
        expires_delta: timedelta | None = None,
    ) -> Token:
        """
        Create a JWT access token for a user.

        Args:
            user: User to create token for
            expires_delta: Optional custom expiration time

        Returns:
            Token object with access_token and token_type
        """
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_access_token_expire_minutes)

        # Build permissions list from role
        permissions: list[str] = []
        if user.role:
            for perm in user.role.permissions:
                permissions.append(f"{perm.resource}:{perm.action}")

        payload = {
            "sub": str(user.id),
            "username": user.username,
            "email": user.email,
            "is_superuser": user.is_superuser,
            "permissions": permissions,
            "exp": expire,
        }

        encoded_jwt = jwt.encode(
            payload,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )

        logger.info(
            "token_created",
            user_id=str(user.id),
            username=user.username,
            expires_at=expire.isoformat(),
        )

        return Token(access_token=encoded_jwt)

    @staticmethod
    def decode_token(token: str) -> TokenPayload | None:
        """
        Decode and validate a JWT token.

        Args:
            token: JWT token string

        Returns:
            TokenPayload if valid, None if invalid
        """
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm],
            )
            return TokenPayload(
                sub=payload["sub"],
                username=payload["username"],
                email=payload["email"],
                is_superuser=payload.get("is_superuser", False),
                permissions=payload.get("permissions", []),
                exp=datetime.fromtimestamp(payload["exp"], tz=timezone.utc) if "exp" in payload else None,
            )
        except JWTError as e:
            logger.warning("token_decode_failed", error=str(e))
            return None

    @staticmethod
    async def authenticate_user(
        db: AsyncSession,
        username: str,
        password: str,
    ) -> User | None:
        """
        Authenticate a user by username and password.

        Args:
            db: Database session
            username: Username or email to authenticate
            password: Plain text password

        Returns:
            User if authentication successful, None otherwise
        """
        # Try to find user by username or email
        stmt = select(User).where((User.username == username) | (User.email == username))
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            logger.warning("auth_user_not_found", username=username)
            return None

        if not AuthService.verify_password(password, user.hashed_password):
            logger.warning("auth_invalid_password", username=username)
            return None

        if not user.is_active:
            logger.warning("auth_user_inactive", username=username)
            return None

        logger.info("auth_success", user_id=str(user.id), username=user.username)
        return user


async def get_current_user(
    token: Annotated[str | None, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> User | None:
    """
    Get the current user from JWT token (optional).

    This dependency does not raise an error if no token is provided.
    Use get_current_active_user for required authentication.

    Args:
        token: JWT token from Authorization header
        db: Database session

    Returns:
        User if authenticated, None otherwise
    """
    if not token:
        return None

    payload = AuthService.decode_token(token)
    if not payload:
        return None

    stmt = select(User).where(User.id == UUID(payload.sub))
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    return user


async def get_current_active_user(
    current_user: Annotated[User | None, Depends(get_current_user)],
) -> User:
    """
    Get the current active user (required).

    Raises 401 if not authenticated or user is inactive.

    Args:
        current_user: User from get_current_user dependency

    Returns:
        Active User object

    Raises:
        HTTPException: 401 if not authenticated or inactive
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive",
        )

    return current_user


def require_permission(resource: str, action: str) -> Callable:
    """
    Create a dependency that requires a specific permission.

    Usage:
        @router.get("/datasets", dependencies=[Depends(require_permission("dataset", "read"))])
        async def list_datasets(...): ...

    Args:
        resource: Resource type (e.g., "dataset", "experiment")
        action: Action type (e.g., "read", "create", "execute")

    Returns:
        FastAPI dependency function
    """

    async def permission_dependency(
        request: Request,
        current_user: Annotated[User, Depends(get_current_active_user)],
    ) -> User:
        """Check if current user has the required permission."""
        if not current_user.has_permission(resource, action):
            logger.warning(
                "permission_denied",
                user_id=str(current_user.id),
                username=current_user.username,
                resource=resource,
                action=action,
                path=request.url.path,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {resource}:{action}",
            )
        return current_user

    return permission_dependency


# Type aliases for common dependencies
CurrentUser = Annotated[User | None, Depends(get_current_user)]
RequiredUser = Annotated[User, Depends(get_current_active_user)]
