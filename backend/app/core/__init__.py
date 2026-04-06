# backend/app/core/__init__.py
from backend.app.core.config import settings
from backend.app.core.logging import get_logger, setup_logging

__all__ = ["settings", "get_logger", "setup_logging"]
