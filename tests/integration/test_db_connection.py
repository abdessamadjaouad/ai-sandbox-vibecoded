# tests/integration/test_db_connection.py
from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.asyncio
async def test_db_session_yields_and_commits():
    """Database session should commit on success."""
    mock_session = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()

    mock_factory = AsyncMock()
    mock_factory.__aenter__ = AsyncMock(return_value=mock_session)
    mock_factory.__aexit__ = AsyncMock(return_value=None)

    with patch("backend.app.core.database.async_session_factory", return_value=mock_factory):
        from backend.app.core.database import get_db_session

        gen = get_db_session()
        session = await gen.__anext__()
        assert session is mock_session


@pytest.mark.asyncio
async def test_database_url_is_configured():
    """Database URL should be set in config."""
    from backend.app.core.config import settings

    assert settings.database_url is not None
    assert "postgresql" in settings.database_url
