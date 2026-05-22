"""FastAPI authentication dependencies.

Provides the get_current_tenant dependency that verifies Clerk JWT,
looks up the Tenant record in DB, and returns a TenantContext.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from context_os.auth.middleware import verify_clerk_jwt
from context_os.config import get_settings
from context_os.core.errors import AuthError
from context_os.db.engine import get_session_factory
from context_os.observability.schema import (
    EVENT,
    StructuredLogRecord,
    emit_structured_log,
)
from context_os.relational.repositories import TenantRepository

_bearer_scheme = HTTPBearer(auto_error=False)


@dataclass
class TenantContext:
    """Authentication context for the current request.

    Attributes:
        tenant_id: Clerk org ID extracted from JWT (e.g. "org_abc123").
        db_tenant_id: Internal UUID primary key from the tenants table.
        user_id: Clerk user subject ID from JWT payload["sub"].
    """

    tenant_id: str
    db_tenant_id: uuid.UUID
    user_id: str = ""


_dev_tenant: TenantContext | None = None


def _get_dev_tenant() -> TenantContext:
    """Return a fixed dev tenant for local bypass mode."""
    global _dev_tenant
    if _dev_tenant is None:
        _dev_tenant = TenantContext(
            tenant_id="org_dev_bypass",
            db_tenant_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
            user_id="user_dev",
        )
    return _dev_tenant


async def get_current_tenant(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> TenantContext:
    """FastAPI dependency: verify JWT and return TenantContext.

    Extracts the Bearer token from the Authorization header, verifies it
    with Clerk, looks up the Tenant row in the database, and returns a
    TenantContext with both the Clerk org ID and the internal DB UUID.

    Args:
        credentials: HTTP Bearer credentials from the Authorization header.

    Returns:
        TenantContext with verified tenant information.

    Raises:
        HTTPException(401): If the token is missing, invalid, or the tenant
                            is not found in the database.
    """
    # Dev bypass: skip JWT verification for local testing
    if get_settings().dev_bypass_auth:
        return _get_dev_tenant()

    if credentials is None:
        emit_structured_log(
            StructuredLogRecord(
                event=EVENT.AUTH_REQUEST_REJECTED,
                message="Missing Authorization header",
                agent_identity="auth-middleware-v1",
                autonomy_level=0,
                tenant_id="",
                duration_ms=0,
                level="WARN",
                metadata={"reason": "no_credentials"},
            )
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "auth_error", "message": "Authorization header required"},
        )

    try:
        auth_result = verify_clerk_jwt(credentials.credentials)
    except AuthError as e:
        emit_structured_log(
            StructuredLogRecord(
                event=EVENT.AUTH_REQUEST_REJECTED,
                message=f"JWT verification failed: {e.message}",
                agent_identity="auth-middleware-v1",
                autonomy_level=0,
                tenant_id="",
                duration_ms=0,
                level="WARN",
                metadata={"reason": "invalid_token", "code": e.code},
            )
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.to_dict(),
        ) from e

    clerk_org_id = auth_result["tenant_id"]

    # Look up the tenant in the database
    factory = get_session_factory()
    async with factory() as session:
        repo = TenantRepository(session)
        tenant = await repo.get_by_clerk_org_id(clerk_org_id)

    if tenant is None:
        emit_structured_log(
            StructuredLogRecord(
                event=EVENT.AUTH_REQUEST_REJECTED,
                message=f"Tenant not found for org ID: {clerk_org_id}",
                agent_identity="auth-middleware-v1",
                autonomy_level=0,
                tenant_id=clerk_org_id,
                duration_ms=0,
                level="WARN",
                metadata={"reason": "tenant_not_found", "clerk_org_id": clerk_org_id},
            )
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "auth_error",
                "message": f"Tenant not registered: {clerk_org_id}",
            },
        )

    user_id = auth_result.get("payload", {}).get("sub", "")

    return TenantContext(
        tenant_id=clerk_org_id,
        db_tenant_id=tenant.id,
        user_id=user_id,
    )
