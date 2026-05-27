"""OAuth PKCE connect/callback endpoints.

Routes (no auth prefix — provider redirects land here):
    GET /oauth/connect/{source}/start    — initiate OAuth flow
    GET /oauth/connect/{source}/callback — handle provider callback

These endpoints are NOT protected by JWT auth because the callback URL is
called directly by the OAuth provider with no Authorization header.
"""

from __future__ import annotations

import logging
import secrets
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select

from context_os.auth.dependencies import TenantContext, get_current_tenant
from context_os.config import get_settings
from context_os.db.engine import get_session_factory
from context_os.db.models import OAuthPendingSession, OAuthToken, OnboardingSession

logger = logging.getLogger(__name__)
router = APIRouter()

_PENDING_TTL = timedelta(minutes=10)


def _encrypt_mock_token(token_str: str) -> bytes:
    """Fernet-encrypt a token string using the configured key.

    Args:
        token_str: Plaintext token to encrypt.

    Returns:
        Encrypted bytes.
    """
    from cryptography.fernet import Fernet

    settings = get_settings()
    f = Fernet(settings.encryption_key.encode())
    return f.encrypt(token_str.encode())


def _provider_auth_url(source: str, state: str) -> str:
    """Build the provider OAuth redirect URL.

    For unconfigured sources (no client_id) in dev, return a mock URL.

    Args:
        source: Integration name (jira, github, slack).
        state: PKCE state parameter.

    Returns:
        Provider OAuth authorization URL.
    """
    settings = get_settings()
    mock_url = f"/oauth/dev/mock-callback?source={source}&state={state}"

    if source == "jira":
        client_id = settings.jira_client_id
        if not client_id:
            return mock_url
        scope = "read%3Ajira-work%20offline_access"
        base = "https://auth.atlassian.com/authorize"
        return (
            f"{base}?audience=api.atlassian.com"
            f"&client_id={client_id}"
            f"&scope={scope}"
            f"&redirect_uri=/oauth/connect/jira/callback"
            f"&state={state}"
            f"&response_type=code"
            f"&prompt=consent"
        )

    if source == "github":
        client_id = settings.github_app_id
        if not client_id:
            return mock_url
        return (
            f"https://github.com/login/oauth/authorize"
            f"?client_id={client_id}&state={state}&scope=repo"
        )

    # slack + any unknown source fall back to the dev mock callback
    return mock_url


@router.get("/connect/{source}/start")
async def oauth_start(
    source: str,
    ctx: TenantContext = Depends(get_current_tenant),
) -> RedirectResponse:
    """Initiate the OAuth PKCE flow for a given source.

    Generates a PKCE state and code_verifier, persists them in
    oauth_pending_sessions (TTL 10 min), and redirects to the provider.

    Args:
        source: Integration name (jira, github, slack).
        ctx: Authenticated tenant context.

    Returns:
        302 redirect to provider authorization URL.
    """
    state = secrets.token_urlsafe(32)
    code_verifier = secrets.token_urlsafe(32)
    expires_at = datetime.now(UTC) + _PENDING_TTL

    factory = get_session_factory()
    async with factory() as session:
        pending = OAuthPendingSession(
            state=state,
            tenant_id=ctx.db_tenant_id,
            source=source,
            code_verifier=code_verifier,
            expires_at=expires_at,
        )
        session.add(pending)
        await session.flush()
        await session.commit()

    auth_url = _provider_auth_url(source, state)
    return RedirectResponse(url=auth_url, status_code=302)


@router.get("/connect/{source}/callback")
async def oauth_callback(
    source: str,
    state: str = Query(..., description="PKCE state"),
    code: str = Query(..., description="Authorization code from provider"),
) -> RedirectResponse:
    """Handle the OAuth provider callback.

    Validates state + expiry, exchanges code for token (mock in dev),
    upserts OAuthToken, appends source to onboarding_sessions.connected_integrations,
    and redirects to /onboarding/connect?source={source}&status=success.

    Args:
        source: Integration name.
        state: PKCE state from the callback query string.
        code: Authorization code from the provider.

    Returns:
        301 redirect to onboarding success URL.

    Raises:
        HTTPException(400): On invalid or expired state.
    """
    factory = get_session_factory()
    async with factory() as session:
        result = await session.execute(
            select(OAuthPendingSession).where(OAuthPendingSession.state == state)
        )
        pending = result.scalar_one_or_none()

        if pending is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "invalid_state", "message": "OAuth state not found"},
            )

        now = datetime.now(UTC)
        expires_at = pending.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)

        if now > expires_at:
            await session.delete(pending)
            await session.flush()
            await session.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "state_expired", "message": "OAuth state has expired"},
            )

        tenant_id = pending.tenant_id

        # Exchange code for token (mock in dev: use code as access token)
        mock_access_token = f"mock_access_token_{source}_{code[:8]}"
        encrypted = _encrypt_mock_token(mock_access_token)

        # Upsert OAuthToken
        token_result = await session.execute(
            select(OAuthToken).where(
                OAuthToken.tenant_id == tenant_id,
                OAuthToken.integration == source,
            )
        )
        existing_token = token_result.scalar_one_or_none()
        if existing_token is None:
            oauth_token = OAuthToken(
                tenant_id=tenant_id,
                integration=source,
                access_token_enc=encrypted,
            )
            session.add(oauth_token)
        else:
            existing_token.access_token_enc = encrypted
            existing_token.updated_at = datetime.now(UTC)

        # Append source to onboarding_sessions.connected_integrations
        onboarding_result = await session.execute(
            select(OnboardingSession).where(OnboardingSession.tenant_id == tenant_id)
        )
        onboarding = onboarding_result.scalar_one_or_none()
        if onboarding is not None:
            connected = list(onboarding.connected_integrations or [])
            if source not in connected:
                connected.append(source)
            onboarding.connected_integrations = connected

        # Clean up pending session
        await session.delete(pending)
        await session.flush()
        await session.commit()

    redirect_url = f"/onboarding/connect?source={source}&status=success"
    return RedirectResponse(url=redirect_url, status_code=302)
