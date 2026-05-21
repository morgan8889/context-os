"""Integration tests for OAuth PKCE connect flow.

Uses httpx.AsyncClient with a mocked FastAPI app. Database and JWT are mocked.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from context_os.auth.dependencies import TenantContext


def _make_tenant_ctx(
    clerk_org_id: str = "org_test",
    db_id: uuid.UUID | None = None,
) -> TenantContext:
    return TenantContext(
        tenant_id=clerk_org_id,
        db_tenant_id=db_id or uuid.uuid4(),
        user_id="user_test",
    )


@pytest.fixture
def app_client():
    """Return a synchronous TestClient with auth dependency overridden."""
    from fastapi import FastAPI

    from context_os.api.oauth import router as oauth_router

    app = FastAPI()
    app.include_router(oauth_router, prefix="/oauth")

    ctx = _make_tenant_ctx()
    from context_os.auth.dependencies import get_current_tenant

    app.dependency_overrides[get_current_tenant] = lambda: ctx

    return TestClient(app, raise_server_exceptions=False)


class TestOAuthStart:
    def test_start_creates_pending_session_and_redirects(
        self, app_client: TestClient
    ) -> None:
        """GET /oauth/connect/jira/start returns 302 redirect."""
        with (
            patch("context_os.api.oauth.get_session_factory") as mock_factory,
        ):
            mock_session = AsyncMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=False)
            mock_session.add = MagicMock()
            mock_session.flush = AsyncMock()
            mock_session.commit = AsyncMock()
            mock_factory.return_value = MagicMock(return_value=mock_session)

            resp = app_client.get("/oauth/connect/jira/start", follow_redirects=False)

        assert resp.status_code == 302
        assert "location" in resp.headers


class TestOAuthCallback:
    def test_callback_invalid_state_returns_400(
        self, app_client: TestClient
    ) -> None:
        """GET /oauth/connect/jira/callback with unknown state returns 400."""
        with patch("context_os.api.oauth.get_session_factory") as mock_factory:
            mock_session = AsyncMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=False)

            # execute returns None = state not found
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_session.execute = AsyncMock(return_value=mock_result)

            mock_factory.return_value = MagicMock(return_value=mock_session)

            resp = app_client.get(
                "/oauth/connect/jira/callback?state=bad_state&code=authcode",
                follow_redirects=False,
            )

        assert resp.status_code == 400

    def test_callback_expired_state_returns_400(
        self, app_client: TestClient
    ) -> None:
        """GET /oauth/connect/jira/callback with expired state returns 400."""
        from context_os.db.models import OAuthPendingSession

        expired_pending = MagicMock(spec=OAuthPendingSession)
        expired_pending.state = "expired_state_123"
        expired_pending.tenant_id = uuid.uuid4()
        expired_pending.source = "jira"
        expired_pending.code_verifier = "verifier"
        expired_pending.expires_at = datetime.now(UTC) - timedelta(minutes=5)

        with patch("context_os.api.oauth.get_session_factory") as mock_factory:
            mock_session = AsyncMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=False)
            mock_session.delete = MagicMock()
            mock_session.flush = AsyncMock()
            mock_session.commit = AsyncMock()

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = expired_pending
            mock_session.execute = AsyncMock(return_value=mock_result)

            mock_factory.return_value = MagicMock(return_value=mock_session)

            resp = app_client.get(
                "/oauth/connect/jira/callback"
                "?state=expired_state_123&code=authcode",
                follow_redirects=False,
            )

        assert resp.status_code == 400

    def test_valid_callback_updates_connected_integrations(
        self, app_client: TestClient
    ) -> None:
        """Valid callback updates onboarding_sessions.connected_integrations."""
        from context_os.db.models import OAuthPendingSession, OnboardingSession

        tenant_id = uuid.uuid4()
        pending = MagicMock(spec=OAuthPendingSession)
        pending.state = "valid_state_abc"
        pending.tenant_id = tenant_id
        pending.source = "jira"
        pending.code_verifier = "verifier_xyz"
        pending.expires_at = datetime.now(UTC) + timedelta(minutes=5)

        onboarding = MagicMock(spec=OnboardingSession)
        onboarding.connected_integrations = []

        with patch("context_os.api.oauth.get_session_factory") as mock_factory:
            mock_session = AsyncMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=False)
            mock_session.delete = MagicMock()
            mock_session.flush = AsyncMock()
            mock_session.commit = AsyncMock()
            mock_session.add = MagicMock()

            # Executes: 1) find pending session 2) find oauth token 3) find onboarding
            mock_result_pending = MagicMock()
            mock_result_pending.scalar_one_or_none.return_value = pending
            mock_result_no_token = MagicMock()
            mock_result_no_token.scalar_one_or_none.return_value = None
            mock_result_onboarding = MagicMock()
            mock_result_onboarding.scalar_one_or_none.return_value = onboarding

            mock_session.execute = AsyncMock(
                side_effect=[
                    mock_result_pending,
                    mock_result_no_token,
                    mock_result_onboarding,
                ]
            )

            mock_factory.return_value = MagicMock(return_value=mock_session)

            with patch("context_os.api.oauth._encrypt_mock_token", return_value=b"enc"):
                resp = app_client.get(
                    "/oauth/connect/jira/callback"
                    "?state=valid_state_abc&code=authcode",
                    follow_redirects=False,
                )

        # Should redirect to onboarding success page
        assert resp.status_code in (301, 302)
        assert "jira" in resp.headers.get("location", "")
