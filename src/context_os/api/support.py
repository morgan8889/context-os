"""Support and admin impersonation endpoints.

Routes:
    POST  /admin/impersonate/{target_clerk_org_id}  — issue impersonation token
    DELETE /admin/impersonate/revoke               — revoke token by JTI
    GET   /support/traces/{operation_id}           — retrieve debug trace
    POST  /support/traces/{operation_id}/export    — download redacted trace
"""

from __future__ import annotations

import copy
import logging
from dataclasses import dataclass, field
from typing import Any

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.responses import Response
from pydantic import BaseModel

from context_os.auth.dependencies import (
    TenantContext,
    require_platform_operator,
)
from context_os.auth.impersonation import (
    issue_impersonation_token,
    revoke_impersonation_token,
)
from context_os.config import get_settings
from context_os.db.engine import get_session_factory
from context_os.relational.repositories import TenantRepository

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Pydantic / dataclass models ───────────────────────────────────────────────


class ImpersonateResponse(BaseModel):
    """Response for POST /admin/impersonate/{target}."""

    token: str
    expires_at: str
    target_tenant_name: str


@dataclass
class DebugTraceSpan:
    """Single span within a debug trace."""

    span_id: str
    name: str
    started_at: str
    ended_at: str | None
    span_type: str
    input: Any = field(default=None)
    output: Any = field(default=None)


@dataclass
class DebugTrace:
    """Full debug trace retrieved from Langfuse."""

    operation_id: str
    name: str
    timestamp: str
    spans: list[DebugTraceSpan] = field(default_factory=list)


class NotFound(Exception):
    """Raised when a trace does not exist in Langfuse."""

    def __init__(self, operation_id: str) -> None:
        super().__init__(f"Trace {operation_id} not found")
        self.operation_id = operation_id


# ── DebugTraceService ─────────────────────────────────────────────────────────


class DebugTraceService:
    """Fetches traces from the Langfuse API."""

    async def get_trace(self, operation_id: str) -> DebugTrace:
        """Fetch a trace by operation ID.

        Args:
            operation_id: Langfuse trace ID.

        Returns:
            DebugTrace with spans ordered by startTime ascending.

        Raises:
            NotFound: When the operation_id does not exist in Langfuse.
        """
        settings = get_settings()
        url = f"{settings.langfuse_host}/api/public/traces/{operation_id}"
        auth = (settings.langfuse_public_key, settings.langfuse_secret_key)

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, auth=auth)
                if resp.status_code == 404:
                    raise NotFound(operation_id)
                resp.raise_for_status()
                data = resp.json()
        except NotFound:
            raise
        except Exception as exc:
            logger.error("Langfuse trace fetch failed for %s: %s", operation_id, exc)
            raise NotFound(operation_id) from exc

        raw_spans: list[dict[str, object]] = data.get("observations", [])
        spans = [
            DebugTraceSpan(
                span_id=str(s.get("id", "")),
                name=str(s.get("name", "")),
                started_at=str(s.get("startTime", "")),
                ended_at=str(s["endTime"]) if "endTime" in s else None,
                span_type=str(s.get("type", "SPAN")),
                input=s.get("input"),
                output=s.get("output"),
            )
            for s in raw_spans
        ]
        spans.sort(key=lambda s: s.started_at or "")

        return DebugTrace(
            operation_id=data.get("id", operation_id),
            name=data.get("name", ""),
            timestamp=data.get("timestamp", ""),
            spans=spans,
        )


def redact_trace(trace: DebugTrace) -> DebugTrace:
    """Return a copy of the trace with LLM content replaced by token counts.

    GENERATION-type spans have their ``input`` and ``output`` replaced with
    ``[REDACTED — N tokens]`` summaries. All other span types are preserved.

    Args:
        trace: The original DebugTrace.

    Returns:
        A new DebugTrace with LLM content redacted.
    """
    redacted_spans: list[DebugTraceSpan] = []
    for span in trace.spans:
        if span.span_type == "GENERATION":
            input_tokens = _count_tokens(span.input)
            output_tokens = _count_tokens(span.output)
            redacted_spans.append(
                DebugTraceSpan(
                    span_id=span.span_id,
                    name=span.name,
                    started_at=span.started_at,
                    ended_at=span.ended_at,
                    span_type=span.span_type,
                    input=f"[REDACTED — {input_tokens} tokens]",
                    output=f"[REDACTED — {output_tokens} tokens]",
                )
            )
        else:
            redacted_spans.append(copy.deepcopy(span))

    return DebugTrace(
        operation_id=trace.operation_id,
        name=trace.name,
        timestamp=trace.timestamp,
        spans=redacted_spans,
    )


def _count_tokens(content: Any) -> int:
    """Rough token count estimate from content length.

    Args:
        content: Any JSON-serialisable content.

    Returns:
        Estimated token count (characters / 4).
    """
    if content is None:
        return 0
    text = str(content)
    return max(1, len(text) // 4)


# ── Admin impersonation endpoints ─────────────────────────────────────────────


@router.post(
    "/admin/impersonate/{target_clerk_org_id}",
    response_model=ImpersonateResponse,
    tags=["Admin"],
)
async def start_impersonation(
    target_clerk_org_id: str,
    ctx: TenantContext = Depends(require_platform_operator),
) -> ImpersonateResponse:
    """Issue a 30-minute impersonation token for the target org.

    Args:
        target_clerk_org_id: Clerk org ID to impersonate.
        ctx: Platform operator TenantContext (enforced by dependency).

    Returns:
        ImpersonateResponse with token, expiry, and target tenant name.

    Raises:
        HTTPException(501): When impersonation_secret is not configured.
        HTTPException(404): When the target org is not found.
    """
    settings = get_settings()
    if not settings.impersonation_secret:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail={
                "code": "not_configured",
                "message": "Impersonation not configured",
            },
        )

    # Look up target tenant name
    factory = get_session_factory()
    async with factory() as session:
        repo = TenantRepository(session)
        tenant = await repo.get_by_clerk_org_id(target_clerk_org_id)

    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "tenant_not_found", "message": "Target org not registered"},
        )

    token = issue_impersonation_token(ctx.user_id, target_clerk_org_id)

    from datetime import UTC, datetime, timedelta

    expires_at = (datetime.now(UTC) + timedelta(seconds=1800)).isoformat()

    return ImpersonateResponse(
        token=token,
        expires_at=expires_at,
        target_tenant_name=tenant.name,
    )


@router.delete("/admin/impersonate/revoke", status_code=204, tags=["Admin"])
async def revoke_impersonation(
    x_impersonation_token: str | None = Header(
        default=None, alias="X-Impersonation-Token"
    ),
    ctx: TenantContext = Depends(require_platform_operator),
) -> Response:
    """Revoke the impersonation token from the X-Impersonation-Token header.

    Args:
        x_impersonation_token: The token to revoke.
        ctx: Authenticated caller context.

    Returns:
        HTTP 204 No Content.

    Raises:
        HTTPException(400): When no token header is present.
    """
    if not x_impersonation_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "missing_token",
                "message": "X-Impersonation-Token required",
            },
        )

    import jwt as pyjwt

    try:
        # Decode without verification just to extract JTI
        unverified = pyjwt.decode(
            x_impersonation_token,
            options={"verify_signature": False},
            algorithms=["HS256"],
        )
        jti = unverified.get("jti", "")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "invalid_token", "message": "Cannot parse token"},
        )

    factory = get_session_factory()
    async with factory() as session:
        await revoke_impersonation_token(jti, session)
        await session.commit()

    return Response(status_code=204)


# ── Support trace endpoints ───────────────────────────────────────────────────


@router.get("/support/traces/{operation_id}", tags=["Support"])
async def get_debug_trace(
    operation_id: str,
    _ctx: TenantContext = Depends(require_platform_operator),
) -> dict[str, object]:
    """Retrieve a full debug trace from Langfuse by operation ID.

    Args:
        operation_id: Langfuse trace ID.

    Returns:
        JSON representation of the DebugTrace.

    Raises:
        HTTPException(404): When the trace is not found.
    """
    svc = DebugTraceService()
    try:
        trace = await svc.get_trace(operation_id)
    except NotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "trace_not_found",
                "message": f"Trace {operation_id} not found",
            },
        )

    return {
        "operation_id": trace.operation_id,
        "name": trace.name,
        "timestamp": trace.timestamp,
        "spans": [
            {
                "span_id": s.span_id,
                "name": s.name,
                "started_at": s.started_at,
                "ended_at": s.ended_at,
                "span_type": s.span_type,
                "input": s.input,
                "output": s.output,
            }
            for s in trace.spans
        ],
    }


@router.post("/support/traces/{operation_id}/export", tags=["Support"])
async def export_debug_trace(
    operation_id: str,
    _ctx: TenantContext = Depends(require_platform_operator),
) -> Response:
    """Download a redacted trace as a JSON attachment.

    Args:
        operation_id: Langfuse trace ID.

    Returns:
        Redacted JSON file with Content-Disposition attachment header.

    Raises:
        HTTPException(404): When the trace is not found.
    """
    import json

    svc = DebugTraceService()
    try:
        trace = await svc.get_trace(operation_id)
    except NotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "trace_not_found",
                "message": f"Trace {operation_id} not found",
            },
        )

    redacted = redact_trace(trace)

    payload = {
        "operation_id": redacted.operation_id,
        "name": redacted.name,
        "timestamp": redacted.timestamp,
        "spans": [
            {
                "span_id": s.span_id,
                "name": s.name,
                "started_at": s.started_at,
                "ended_at": s.ended_at,
                "span_type": s.span_type,
                "input": s.input,
                "output": s.output,
            }
            for s in redacted.spans
        ],
    }

    return Response(
        content=json.dumps(payload, indent=2),
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="trace-{operation_id}.json"'
        },
    )
