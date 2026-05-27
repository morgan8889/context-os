"""Impersonation JWT issue / verify / revoke.

Impersonation tokens are HS256 JWTs signed with a dedicated secret that is
separate from the Clerk RS256 signing key. They expire in 30 minutes and can
be revoked by inserting a row into the revoked_impersonation_tokens table.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from context_os.config import get_settings
from context_os.db.models import RevokedImpersonationToken

_ALGORITHM = "HS256"
_TOKEN_TTL = timedelta(seconds=1800)  # 30 minutes


def issue_impersonation_token(
    operator_user_id: str,
    target_clerk_org_id: str,
) -> str:
    """Issue a short-lived HS256 impersonation token.

    Args:
        operator_user_id: Clerk user ID of the platform operator performing
                          the impersonation.
        target_clerk_org_id: Clerk org ID of the tenant being impersonated.

    Returns:
        Signed JWT string.

    Raises:
        RuntimeError: If ``settings.impersonation_secret`` is empty.
    """
    settings = get_settings()
    if not settings.impersonation_secret:
        raise RuntimeError(
            "impersonation_secret is not configured; "
            "set IMPERSONATION_SECRET in the environment"
        )

    now = datetime.now(UTC)
    payload = {
        "sub": operator_user_id,
        "impersonating_tenant_id": target_clerk_org_id,
        "impersonator": True,
        "jti": str(uuid.uuid4()),
        "iat": int(now.timestamp()),
        "exp": int((now + _TOKEN_TTL).timestamp()),
    }
    return jwt.encode(payload, settings.impersonation_secret, algorithm=_ALGORITHM)


async def verify_impersonation_token(
    token: str,
    session: AsyncSession,
) -> dict[str, object]:
    """Verify an impersonation JWT and return its claims.

    Checks:
    1. HS256 signature validity
    2. Token expiry
    3. JTI not in ``revoked_impersonation_tokens``

    Args:
        token: Raw JWT string from the X-Impersonation-Token header.
        session: SQLAlchemy AsyncSession for the revocation check.

    Returns:
        Decoded JWT payload dict.

    Raises:
        jwt.InvalidTokenError: On invalid signature, expiry, or revoked JTI.
    """
    settings = get_settings()

    try:
        claims = jwt.decode(
            token,
            settings.impersonation_secret,
            algorithms=[_ALGORITHM],
        )
    except jwt.PyJWTError as exc:
        raise jwt.InvalidTokenError(str(exc)) from exc

    # Check revocation table
    jti = str(claims.get("jti", ""))
    result = await session.execute(
        select(RevokedImpersonationToken).where(
            RevokedImpersonationToken.jti == jti
        )
    )
    revoked_row = result.scalar_one_or_none()
    if revoked_row is not None:
        raise jwt.InvalidTokenError(f"Impersonation token {jti} has been revoked")

    return claims


async def revoke_impersonation_token(
    jti: str,
    session: AsyncSession,
) -> None:
    """Add a JTI to the revocation blocklist.

    Args:
        jti: JWT ID claim from the token to revoke.
        session: SQLAlchemy AsyncSession for the insert.
    """
    row = RevokedImpersonationToken(
        jti=jti,
        revoked_at=datetime.now(UTC),
    )
    session.add(row)
    await session.flush()
