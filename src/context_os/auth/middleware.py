"""Clerk JWT verification and tenant ID extraction.

Uses the clerk-backend-api SDK for JWT verification with JWKS caching.
Tenant ID is extracted from the Clerk v2 JWT org claim: payload["o"]["id"].
The top-level org_id claim is deprecated as of April 2025.
"""

from __future__ import annotations

import logging
from typing import Any

from context_os.config import get_settings
from context_os.core.errors import AuthError

logger = logging.getLogger(__name__)


def verify_clerk_jwt(token: str) -> dict[str, Any]:
    """Verify a Clerk JWT and extract the tenant ID.

    Uses the Clerk SDK's authenticate_request() for RS256 JWT verification
    with automatic JWKS fetching and caching.

    Args:
        token: Raw JWT string (without 'Bearer ' prefix).

    Returns:
        Dict with at least 'tenant_id' (str) and 'payload' (dict) keys.

    Raises:
        AuthError: If the token is invalid, expired, or missing the org claim.
    """
    if not token or not token.strip():
        raise AuthError(
            code="auth_error",
            message="Authorization token is required",
        )

    settings = get_settings()

    try:
        # Use clerk SDK to verify the JWT
        from clerk_backend_api import Clerk
        from clerk_backend_api.models import RequestState

        clerk_client = Clerk(bearer_auth=settings.clerk_secret_key)

        # Create a minimal mock request object for authenticate_request
        # The SDK needs the Authorization header
        class _MockRequest:
            def __init__(self, auth_token: str) -> None:
                self.headers = {"Authorization": f"Bearer {auth_token}"}

        mock_request = _MockRequest(token)

        # Verify the JWT
        request_state: RequestState = clerk_client.authenticate_request(  # type: ignore[attr-defined]
            mock_request,  # type: ignore[arg-type]
        )

        if not request_state.is_signed_in:
            raise AuthError(
                code="auth_error",
                message="Invalid or expired JWT token",
            )

        payload = request_state.payload or {}

    except AuthError:
        raise
    except ImportError:
        logger.warning("Clerk SDK not available, falling back to manual JWT decode")
        payload = _decode_jwt_payload(token)
    except Exception as e:
        raise AuthError(
            code="auth_error",
            message=f"JWT verification failed: {e}",
        ) from e

    # Extract tenant ID from Clerk v2 org claim: payload["o"]["id"]
    # NOT top-level org_id (deprecated April 2025)
    org_claim = payload.get("o", {})
    if isinstance(org_claim, dict):
        tenant_id = org_claim.get("id")
    else:
        tenant_id = None

    if not tenant_id:
        raise AuthError(
            code="auth_error",
            message=(
                "JWT missing organization claim (o.id)"
                " — ensure you are authenticated with an org context"
            ),
        )

    return {
        "tenant_id": str(tenant_id),
        "payload": payload,
    }


def _decode_jwt_payload(token: str) -> dict[str, Any]:
    """Decode JWT payload without verification (for extracting claims only).

    WARNING: This does NOT verify the signature. Used only as a fallback
    when the Clerk SDK is unavailable (e.g. in testing environments).

    Args:
        token: Raw JWT string.

    Returns:
        Decoded payload dict.

    Raises:
        AuthError: If the token cannot be decoded.
    """
    import base64
    import json

    try:
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("Not a valid JWT format")

        # Add padding if needed
        payload_part = parts[1]
        padding = 4 - len(payload_part) % 4
        if padding != 4:
            payload_part += "=" * padding

        decoded = base64.urlsafe_b64decode(payload_part)
        return dict(json.loads(decoded))
    except Exception as e:
        raise AuthError(
            code="auth_error",
            message=f"Failed to decode JWT: {e}",
        ) from e
