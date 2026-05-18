"""Inbox API endpoints for reviewing and acting on approval items.

GET  /inbox            — list pending ApprovalItems with preview
GET  /inbox/{item_id}  — full ApprovalItem detail
POST /inbox/{item_id}/approve — approve an item (promotes to graph)
POST /inbox/{item_id}/reject  — reject an item (recorded as provenance)

All routes require Clerk JWT authentication via get_current_tenant dependency.
"""

from __future__ import annotations

import difflib
import json
import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, cast

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from context_os.auth.dependencies import TenantContext, get_current_tenant
from context_os.db.engine import get_session_factory
from context_os.graph.client import get_age_pool
from context_os.graph.mutations import (
    promote_briefing_to_artifact,
    promote_dependency_edge,
    promote_risk_node,
)
from context_os.observability.tracer import get_current_trace_id, get_tracer
from context_os.relational.repositories import ApprovalItemRepository

logger = logging.getLogger(__name__)
router = APIRouter()
_tracer = None


def _get_tracer() -> Any:
    global _tracer
    if _tracer is None:
        try:
            _tracer = get_tracer("context_os.api.inbox")
        except RuntimeError:
            pass
    return _tracer


# ── Response schemas ──────────────────────────────────────────────────────────


class ApprovalItemSummary(BaseModel):
    """Summary representation of an ApprovalItem for inbox listing."""

    id: str
    tenant_id: str
    item_type: str
    status: str
    preview: str
    failure_flag_count: int
    stale: bool
    created_at: str
    acted_at: str | None = None


class ApprovalItemDetail(BaseModel):
    """Full detail representation of an ApprovalItem."""

    id: str
    tenant_id: str
    item_type: str
    status: str
    content: dict[str, Any]
    failure_flags: dict[str, Any] | None = None
    operator_id: str | None = None
    acted_at: str | None = None
    rejection_reason: str | None = None
    edit_delta: dict[str, Any] | None = None
    run_id: str | None = None
    graph_node_id: str | None = None
    workflow_thread_id: str | None = None
    created_at: str
    updated_at: str


class InboxListResponse(BaseModel):
    """Response schema for the inbox list endpoint."""

    items: list[ApprovalItemSummary]
    pending_count: int
    total: int


class ApproveRequest(BaseModel):
    """Request body for the approve endpoint."""

    edited_content: dict[str, Any] | None = None
    operator_id: str = "system"


class RejectRequest(BaseModel):
    """Request body for the reject endpoint."""

    reason: str | None = None
    operator_id: str = "system"


# ── Helpers ───────────────────────────────────────────────────────────────────

_STALE_THRESHOLD = timedelta(hours=24)


def _is_stale(created_at: datetime) -> bool:
    """Return True if the item has been pending for more than 24 hours."""
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=UTC)
    return (datetime.now(UTC) - created_at) > _STALE_THRESHOLD


def _extract_preview(content: dict[str, Any]) -> str:
    """Extract a 200-char preview from the item's primary content field."""
    # Try common content fields in priority order
    for key in ("sections", "description", "text"):
        val = content.get(key)
        if val:
            text = json.dumps(val) if not isinstance(val, str) else val
            return text[:200]
    return str(content)[:200]


def _compute_edit_delta(
    original: dict[str, Any],
    final: dict[str, Any],
) -> dict[str, Any]:
    """Compute a token-level diff between original and final content.

    Uses difflib.SequenceMatcher to compute the similarity ratio and
    identify which top-level keys changed.

    Args:
        original: Original content dict before operator edits.
        final: Final content dict after operator edits.

    Returns:
        Dict with original_text, final_text, similarity_ratio, changed_keys.
    """
    orig_str = json.dumps(original, sort_keys=True)
    final_str = json.dumps(final, sort_keys=True)

    matcher = difflib.SequenceMatcher(None, orig_str, final_str)
    ratio = matcher.ratio()

    changed_keys = [
        k
        for k in set(list(original.keys()) + list(final.keys()))
        if original.get(k) != final.get(k)
    ]

    return {
        "original_tokens": len(orig_str.split()),
        "final_tokens": len(final_str.split()),
        "similarity_ratio": round(ratio, 4),
        "changed_sections": changed_keys,
    }


# ── GET /inbox ────────────────────────────────────────────────────────────────


@router.get("", response_model=InboxListResponse)
async def list_inbox(
    status_filter: str | None = Query(
        default=None, alias="status", description="pending | approved | rejected"
    ),
    item_type: str | None = Query(
        default=None, description="briefing_draft | proposed_dependency | proposed_risk"
    ),
    stale_only: bool = Query(
        default=False, description="Only return items pending > 24h"
    ),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    tenant: TenantContext = Depends(get_current_tenant),
) -> InboxListResponse:
    """List ApprovalItems in the inbox for the current tenant.

    Args:
        status_filter: Filter by item status.
        item_type: Filter by item type.
        stale_only: Return only items pending more than 24 hours.
        limit: Max items to return.
        offset: Pagination offset.
        tenant: Authenticated tenant context.

    Returns:
        InboxListResponse with items list, pending count, and total.
    """
    factory = get_session_factory()
    async with factory() as session:
        repo = ApprovalItemRepository(session)
        items = await repo.list_by_tenant(
            tenant_id=tenant.tenant_id,
            status=status_filter,
            item_type=item_type,
            stale_only=stale_only,
            limit=limit,
            offset=offset,
        )

        # Count pending items for the response header
        pending_items = await repo.list_by_tenant(
            tenant_id=tenant.tenant_id,
            status="pending",
            limit=1000,
        )
        pending_count = len(pending_items)

    summaries = [
        ApprovalItemSummary(
            id=str(item.id),
            tenant_id=item.tenant_id,
            item_type=item.item_type,
            status=item.status,
            preview=_extract_preview(item.content),
            failure_flag_count=(
                len(cast(list[Any], item.failure_flags.get("flags", [])))
                if item.failure_flags
                else 0
            ),
            stale=_is_stale(item.created_at) and item.status == "pending",
            created_at=item.created_at.isoformat(),
            acted_at=item.acted_at.isoformat() if item.acted_at else None,
        )
        for item in items
    ]

    return InboxListResponse(
        items=summaries,
        pending_count=pending_count,
        total=len(summaries),
    )


# ── GET /inbox/{item_id} ──────────────────────────────────────────────────────


@router.get("/{item_id}", response_model=ApprovalItemDetail)
async def get_inbox_item(
    item_id: uuid.UUID,
    tenant: TenantContext = Depends(get_current_tenant),
) -> ApprovalItemDetail:
    """Get full detail for an ApprovalItem.

    Args:
        item_id: UUID of the ApprovalItem.
        tenant: Authenticated tenant context.

    Returns:
        Full ApprovalItemDetail including failure_flags and content.

    Raises:
        HTTPException(404): If item not found for this tenant.
    """
    factory = get_session_factory()
    async with factory() as session:
        repo = ApprovalItemRepository(session)
        item = await repo.get_by_id(item_id, tenant.tenant_id)

    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "not_found",
                "message": f"ApprovalItem {item_id} not found",
            },
        )

    return ApprovalItemDetail(
        id=str(item.id),
        tenant_id=item.tenant_id,
        item_type=item.item_type,
        status=item.status,
        content=item.content,
        failure_flags=item.failure_flags,
        operator_id=item.operator_id,
        acted_at=item.acted_at.isoformat() if item.acted_at else None,
        rejection_reason=item.rejection_reason,
        edit_delta=item.edit_delta,
        run_id=str(item.run_id) if item.run_id else None,
        graph_node_id=str(item.graph_node_id) if item.graph_node_id else None,
        workflow_thread_id=item.workflow_thread_id,
        created_at=item.created_at.isoformat(),
        updated_at=item.updated_at.isoformat(),
    )


# ── POST /inbox/{item_id}/approve ─────────────────────────────────────────────


@router.post("/{item_id}/approve", response_model=ApprovalItemDetail)
async def approve_item(
    item_id: uuid.UUID,
    body: ApproveRequest | None = None,
    tenant: TenantContext = Depends(get_current_tenant),
) -> ApprovalItemDetail:
    """Approve a pending ApprovalItem and promote it to the canonical graph.

    Validates that the item exists and is in pending status, computes an edit
    delta if edited_content is provided, calls the appropriate graph promotion
    function, and updates the ApprovalItem to approved status.

    Args:
        item_id: UUID of the ApprovalItem to approve.
        body: Optional request body with edited_content and operator_id.
        tenant: Authenticated tenant context.

    Returns:
        Updated ApprovalItemDetail with status=approved.

    Raises:
        HTTPException(404): If item not found.
        HTTPException(400): If item is not in pending status.
        HTTPException(500): If graph promotion fails.
    """
    req = body or ApproveRequest()
    tracer = _get_tracer()
    trace_id = get_current_trace_id()

    factory = get_session_factory()
    async with factory() as session:
        repo = ApprovalItemRepository(session)
        item = await repo.get_by_id(item_id, tenant.tenant_id)

        if item is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "not_found", "message": f"Item {item_id} not found"},
            )

        if item.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "invalid_status",
                    "message": (
                        f"Item {item_id} is not pending (status={item.status}). "
                        "Only pending items can be approved."
                    ),
                },
            )

        # Determine final content (original or edited)
        final_content = req.edited_content if req.edited_content else item.content
        edit_delta = None
        if req.edited_content and req.edited_content != item.content:
            edit_delta = _compute_edit_delta(item.content, req.edited_content)

        # Promote to graph based on item_type
        pool = get_age_pool()
        graph_node_id: uuid.UUID | None = None

        try:
            if item.item_type == "briefing_draft":
                node_id_str = await promote_briefing_to_artifact(
                    tenant_id=tenant.tenant_id,
                    approved_content=final_content,
                    approval_item_id=str(item_id),
                    operator_id=req.operator_id,
                    age_pool=pool,
                )
                graph_node_id = uuid.UUID(node_id_str) if node_id_str else None

            elif item.item_type == "proposed_risk":
                node_id_str = await promote_risk_node(
                    tenant_id=tenant.tenant_id,
                    approved_content=final_content,
                    approval_item_id=str(item_id),
                    operator_id=req.operator_id,
                    age_pool=pool,
                )
                graph_node_id = uuid.UUID(node_id_str) if node_id_str else None

            elif item.item_type == "proposed_dependency":
                await promote_dependency_edge(
                    tenant_id=tenant.tenant_id,
                    approved_content=final_content,
                    approval_item_id=str(item_id),
                    operator_id=req.operator_id,
                    age_pool=pool,
                )
                graph_node_id = None  # Edge promotions have no node ID

            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "code": "unknown_item_type",
                        "message": f"Unknown item_type: {item.item_type}",
                    },
                )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "Graph promotion failed: item_id=%s type=%s error=%s",
                item_id,
                item.item_type,
                e,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "code": "promotion_failed",
                    "message": f"Graph promotion failed: {e}",
                    "trace_id": trace_id,
                },
            ) from e

        # Update ApprovalItem to approved
        updated = await repo.update_approval(
            item_id=item_id,
            tenant_id=tenant.tenant_id,
            operator_id=req.operator_id,
            graph_node_id=graph_node_id,
            edit_delta=edit_delta,
        )
        await session.commit()

    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": f"Item {item_id} not found"},
        )

    # Emit OTEL span for governance observability
    if tracer:
        with tracer.start_as_current_span("context_os.inbox.approve") as span:
            span.set_attribute("context_os.agent_identity", "inbox-api")
            span.set_attribute("context_os.autonomy_level", 0)
            span.set_attribute("context_os.tenant_id", tenant.tenant_id)
            span.set_attribute(
                "context_os.governance_markers",
                '["operator_approved"]',
            )
            span.set_attribute(
                "context_os.input_summary",
                f"item_id={item_id} type={item.item_type}",
            )
            span.set_attribute(
                "context_os.output_summary",
                f"graph_node_id={graph_node_id}",
            )

    return ApprovalItemDetail(
        id=str(updated.id),
        tenant_id=updated.tenant_id,
        item_type=updated.item_type,
        status=updated.status,
        content=updated.content,
        failure_flags=updated.failure_flags,
        operator_id=updated.operator_id,
        acted_at=updated.acted_at.isoformat() if updated.acted_at else None,
        rejection_reason=updated.rejection_reason,
        edit_delta=updated.edit_delta,
        run_id=str(updated.run_id) if updated.run_id else None,
        graph_node_id=str(updated.graph_node_id) if updated.graph_node_id else None,
        workflow_thread_id=updated.workflow_thread_id,
        created_at=updated.created_at.isoformat(),
        updated_at=updated.updated_at.isoformat(),
    )


# ── POST /inbox/{item_id}/reject ──────────────────────────────────────────────


@router.post("/{item_id}/reject", response_model=ApprovalItemDetail)
async def reject_item(
    item_id: uuid.UUID,
    body: RejectRequest | None = None,
    tenant: TenantContext = Depends(get_current_tenant),
) -> ApprovalItemDetail:
    """Reject a pending ApprovalItem.

    Records the rejection with an optional reason. No graph write is performed.
    The item remains as a provenance log entry.

    Args:
        item_id: UUID of the ApprovalItem to reject.
        body: Optional request body with reason and operator_id.
        tenant: Authenticated tenant context.

    Returns:
        Updated ApprovalItemDetail with status=rejected.

    Raises:
        HTTPException(404): If item not found.
        HTTPException(400): If item is not in pending status.
    """
    req = body or RejectRequest()
    tracer = _get_tracer()

    factory = get_session_factory()
    async with factory() as session:
        repo = ApprovalItemRepository(session)
        item = await repo.get_by_id(item_id, tenant.tenant_id)

        if item is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "not_found", "message": f"Item {item_id} not found"},
            )

        if item.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "invalid_status",
                    "message": (
                        f"Item {item_id} is not pending (status={item.status}). "
                        "Only pending items can be rejected."
                    ),
                },
            )

        updated = await repo.update_rejection(
            item_id=item_id,
            tenant_id=tenant.tenant_id,
            operator_id=req.operator_id,
            reason=req.reason,
        )
        await session.commit()

    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": f"Item {item_id} not found"},
        )

    # Emit OTEL span with rejected governance marker
    if tracer:
        with tracer.start_as_current_span("context_os.inbox.reject") as span:
            span.set_attribute("context_os.agent_identity", "inbox-api")
            span.set_attribute("context_os.autonomy_level", 0)
            span.set_attribute("context_os.tenant_id", tenant.tenant_id)
            span.set_attribute(
                "context_os.governance_markers",
                '["rejected"]',
            )
            span.set_attribute(
                "context_os.input_summary",
                f"item_id={item_id} type={item.item_type}",
            )
            span.set_attribute(
                "context_os.output_summary",
                f"rejected reason={req.reason or 'none'}",
            )

    return ApprovalItemDetail(
        id=str(updated.id),
        tenant_id=updated.tenant_id,
        item_type=updated.item_type,
        status=updated.status,
        content=updated.content,
        failure_flags=updated.failure_flags,
        operator_id=updated.operator_id,
        acted_at=updated.acted_at.isoformat() if updated.acted_at else None,
        rejection_reason=updated.rejection_reason,
        edit_delta=updated.edit_delta,
        run_id=str(updated.run_id) if updated.run_id else None,
        graph_node_id=None,
        workflow_thread_id=updated.workflow_thread_id,
        created_at=updated.created_at.isoformat(),
        updated_at=updated.updated_at.isoformat(),
    )
