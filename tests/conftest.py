"""Pytest fixtures for Context-OS tests.

Provides database, tenant, and mock OAuth fixtures for all test types.
"""

from __future__ import annotations

import asyncio
import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

# ── Event loop ─────────────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def event_loop_policy() -> asyncio.DefaultEventLoopPolicy:
    """Use the default asyncio event loop policy."""
    return asyncio.DefaultEventLoopPolicy()


# ── Settings override ──────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def mock_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """Override settings for tests to avoid requiring real credentials."""
    monkeypatch.setenv(
        "DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test"
    )
    monkeypatch.setenv("CLERK_SECRET_KEY", "sk_test_fake")
    monkeypatch.setenv("CLERK_PUBLISHABLE_KEY", "pk_test_fake")
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-lf-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-lf-test")
    monkeypatch.setenv("ENCRYPTION_KEY", "dGVzdGtleS10ZXN0a2V5LXRlc3RrZXktdGVzdGtleT0=")
    monkeypatch.setenv("GITHUB_APP_ID", "12345")
    monkeypatch.setenv("GITHUB_APP_PRIVATE_KEY_PATH", "./test.pem")
    monkeypatch.setenv("GITHUB_INSTALLATION_ID", "67890")


# ── Tenant fixtures ────────────────────────────────────────────────────────────


@pytest.fixture
def tenant_a_clerk_id() -> str:
    """Clerk org ID for test tenant A."""
    return f"org_tenant_a_{uuid.uuid4().hex[:8]}"


@pytest.fixture
def tenant_b_clerk_id() -> str:
    """Clerk org ID for test tenant B."""
    return f"org_tenant_b_{uuid.uuid4().hex[:8]}"


@pytest.fixture
def tenant_a_db_id() -> uuid.UUID:
    """Internal UUID for test tenant A."""
    return uuid.uuid4()


@pytest.fixture
def tenant_b_db_id() -> uuid.UUID:
    """Internal UUID for test tenant B."""
    return uuid.uuid4()


# ── Mock fixtures ──────────────────────────────────────────────────────────────


@pytest.fixture
def mock_age_pool() -> MagicMock:
    """Mock AGE asyncpg pool."""
    pool = MagicMock()
    pool.acquire = AsyncMock(
        return_value=MagicMock(__aenter__=AsyncMock(), __aexit__=AsyncMock())
    )
    return pool


@pytest.fixture
def mock_db_session() -> AsyncMock:
    """Mock SQLAlchemy AsyncSession."""
    session = AsyncMock(spec=AsyncSession)
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.execute = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    return session


@pytest.fixture
def mock_oauth_expire_middleware() -> Any:
    """Mock OAuth middleware that injects 401 after first page of requests.

    Returns a context manager that patches httpx to simulate token expiry.
    """
    call_count = [0]

    class _MockHTTPResponse:
        def __init__(self, status_code: int, data: Any = None) -> None:
            self.status_code = status_code
            self._data = data or {}
            self.headers = {"Content-Type": "application/json"}

        def json(self) -> Any:
            return self._data

        def raise_for_status(self) -> None:
            if self.status_code >= 400:
                import httpx

                raise httpx.HTTPStatusError(
                    f"HTTP {self.status_code}",
                    request=MagicMock(),
                    response=MagicMock(status_code=self.status_code),
                )

    async def _mock_get(*args: Any, **kwargs: Any) -> _MockHTTPResponse:
        call_count[0] += 1
        if call_count[0] > 1:
            return _MockHTTPResponse(401, {"message": "Bad credentials"})
        return _MockHTTPResponse(200, [])

    return patch("httpx.AsyncClient.get", side_effect=_mock_get)
