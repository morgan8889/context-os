"""Dependency Mapper API endpoints.

POST /mapper/scan — trigger a dependency discovery scan
GET  /mapper/scan/status — check if a scan is active for the current tenant

All routes require Clerk JWT authentication via get_current_tenant dependency.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel

from context_os.auth.dependencies import TenantContext, get_current_tenant
from context_os.db.engine import get_session_factory
from context_os.graph.client import get_age_pool
from context_os.observability.tracer import get_current_trace_id, get_tracer
from context_os.workflows.dependency import DependencyWorkflow, MapperScanStatus

logger = logging.getLogger(__name__)
router = APIRouter()
_tracer = None


def _get_tracer() -> Any:
    global _tracer
    if _tracer is None:
        try:
            _tracer = get_tracer("context_os.api.mapper")
        except RuntimeError:
            pass
    return _tracer


# ── Response schemas ──────────────────────────────────────────────────────────


class MapperScanRequest(BaseModel):
    """Request body for POST /mapper/scan."""

    max_depth: int = 3
    focus_node_id: str | None = None


class MapperScanResponse(BaseModel):
    """Response schema for the mapper scan endpoint."""

    tenant_id: str
    status: str
    message: str
    trace_id: str | None = None


class MapperScanStatusResponse(BaseModel):
    """Response schema for the mapper scan status endpoint."""

    tenant_id: str
    active: bool


# ── Background task ───────────────────────────────────────────────────────────


async def _run_scan_background(
    tenant_id: str,
    max_depth: int,
    focus_node_id: str | None,
) -> None:
    """Background task: run a dependency mapper scan for a tenant.

    Creates a new DB session (independent of the request session) and runs
    the DependencyWorkflow. Logs the result on completion.

    Args:
        tenant_id: Clerk org ID.
        max_depth: Maximum graph traversal depth.
        focus_node_id: Optional node ID to focus traversal from.
    """
    try:
        pool = get_age_pool()
        checkpointer = _get_checkpointer()

        factory = get_session_factory()
        async with factory() as session:
            workflow = DependencyWorkflow(
                age_pool=pool,
                session=session,
                checkpointer=checkpointer,
            )
            result: MapperScanStatus = await workflow.scan(
                tenant_id=tenant_id,
                max_depth=max_depth,
                focus_node_id=focus_node_id,
            )

        logger.info(
            "Mapper background scan complete: tenant=%s proposed=%d status=%s",
            tenant_id,
            result.proposed_count,
            result.status,
        )

    except Exception as exc:
        logger.error(
            "Mapper background scan crashed: tenant=%s error=%s",
            tenant_id,
            exc,
        )


def _get_checkpointer() -> Any:
    """Return the LangGraph AsyncPostgresSaver from app state (if available).

    Returns:
        Checkpointer instance or None if not initialized.
    """
    try:
        from context_os.main import app

        return getattr(app.state, "langgraph_checkpointer", None)
    except Exception:
        return None


# ── POST /mapper/scan ─────────────────────────────────────────────────────────


@router.post("/scan", response_model=MapperScanResponse, status_code=202)
async def trigger_scan(
    background_tasks: BackgroundTasks,
    body: MapperScanRequest | None = None,
    tenant: TenantContext = Depends(get_current_tenant),
) -> MapperScanResponse:
    """Trigger a dependency discovery scan for the current tenant.

    Validates that no scan is currently active (409 if found), validates that
    the graph contains at least 2 Initiative nodes (400 if not), then runs
    the DependencyWorkflow as a background task.

    Args:
        background_tasks: FastAPI background task queue.
        body: Optional request body with max_depth and focus_node_id.
        tenant: Authenticated tenant context.

    Returns:
        202 Accepted with MapperScanResponse (status=scanning).

    Raises:
        HTTPException(409): If a scan is already active for this tenant.
        HTTPException(400): If fewer than 2 Initiative nodes exist in the graph.
    """
    req = body or MapperScanRequest()
    trace_id = get_current_trace_id()

    # 1. Check for active scan
    if DependencyWorkflow.is_active(tenant.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "scan_already_active",
                "message": (
                    "A dependency scan is already running for this tenant. "
                    "Wait for it to complete before starting a new scan."
                ),
            },
        )

    # 2. Validate graph has at least 2 Initiative nodes
    try:
        pool = get_age_pool()
        from context_os.graph.client import run_cypher

        rows = await run_cypher(
            pool,
            """
            MATCH (i:Initiative)
            WHERE i.tenant_id = $tenant_id
            RETURN count(i) AS cnt
            """,
            params={"tenant_id": tenant.tenant_id},
            columns=[("cnt", "agtype")],
        )
        initiative_count = int(rows[0].get("cnt", 0)) if rows else 0
    except Exception as exc:
        logger.warning(
            "Failed to count Initiative nodes for tenant=%s: %s",
            tenant.tenant_id,
            exc,
        )
        initiative_count = 0

    if initiative_count < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "insufficient_initiatives",
                "message": (
                    "At least 2 Initiative nodes are required to discover "
                    f"dependencies (found {initiative_count}). "
                    "Ingest data and ensure Initiative nodes exist in the "
                    "graph."
                ),
            },
        )

    # 3. Enqueue background scan
    background_tasks.add_task(
        _run_scan_background,
        tenant_id=tenant.tenant_id,
        max_depth=req.max_depth,
        focus_node_id=req.focus_node_id,
    )

    logger.info(
        "Mapper scan enqueued: tenant=%s max_depth=%d",
        tenant.tenant_id,
        req.max_depth,
    )

    return MapperScanResponse(
        tenant_id=tenant.tenant_id,
        status="scanning",
        message=(
            f"Dependency scan started with max_depth={req.max_depth}. "
            "Poll GET /inbox?item_type=proposed_dependency to see results."
        ),
        trace_id=trace_id,
    )


# ── GET /mapper/scan/status ───────────────────────────────────────────────────


@router.get("/scan/status", response_model=MapperScanStatusResponse)
async def get_scan_status(
    tenant: TenantContext = Depends(get_current_tenant),
) -> MapperScanStatusResponse:
    """Check whether a dependency scan is currently active for this tenant.

    Args:
        tenant: Authenticated tenant context.

    Returns:
        MapperScanStatusResponse with active flag.
    """
    return MapperScanStatusResponse(
        tenant_id=tenant.tenant_id,
        active=DependencyWorkflow.is_active(tenant.tenant_id),
    )
