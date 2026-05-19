"""Briefing API endpoints.

POST /briefing/generate   — trigger weekly briefing generation
GET  /briefing/status/{run_id} — poll briefing run status

All routes require Clerk JWT authentication via get_current_tenant dependency.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel

from context_os.auth.dependencies import TenantContext, get_current_tenant
from context_os.db.engine import get_session_factory
from context_os.graph.client import get_age_pool
from context_os.observability.tracer import get_current_trace_id, get_tracer
from context_os.relational.repositories import BriefingRunRepository

logger = logging.getLogger(__name__)
router = APIRouter()
_tracer = None


def _get_tracer() -> Any:
    global _tracer
    if _tracer is None:
        try:
            _tracer = get_tracer("context_os.api.briefing")
        except RuntimeError:
            pass
    return _tracer


# ── Response schemas ──────────────────────────────────────────────────────────


class BriefingGenerateRequest(BaseModel):
    """Request body for POST /briefing/generate."""

    window_days: int = 7
    trigger_type: str = "manual"


class BriefingRunStatus(BaseModel):
    """Status response for a briefing run."""

    run_id: str
    status: str
    tenant_id: str
    approval_item_id: str | None = None
    cost_tokens: int | None = None
    latency_ms: int | None = None
    error: str | None = None
    window_start: str | None = None
    window_end: str | None = None
    trace_id: str | None = None


# ── Background task ───────────────────────────────────────────────────────────


async def _run_briefing_background(
    tenant_id: str,
    db_tenant_id: str,
    run_id: uuid.UUID,
    window_days: int,
    trigger_type: str,
) -> None:
    """Background task: run the full briefing workflow for a tenant.

    Creates a new DB session (independent of the request session) and runs
    the BriefingWorkflow, updating the BriefingRun record on completion.

    Args:
        tenant_id: Clerk org ID.
        db_tenant_id: Internal DB UUID string.
        run_id: UUID of the pre-created BriefingRun record.
        window_days: Briefing window in days.
        trigger_type: manual | scheduled.
    """
    try:
        pool = get_age_pool()
        checkpointer = _get_checkpointer()

        factory = get_session_factory()
        async with factory() as session:
            # The workflow will update the existing BriefingRun (already created)
            # We need to pass the existing run_id so it updates rather than creates
            run_repo = BriefingRunRepository(session)
            import time

            from context_os.agents.synthesizer.agent import SynthesizerAgent

            agent = SynthesizerAgent(
                tenant_id=tenant_id,
                db_tenant_id=db_tenant_id,
                age_pool=pool,
                session=session,
                checkpointer=checkpointer,
            )

            start_time = time.monotonic()
            try:
                final_state = await agent.run(
                    window_days=window_days,
                    run_id=str(run_id),
                )
                elapsed_ms = int((time.monotonic() - start_time) * 1000)
                cost_tokens = final_state.get("cost_tokens", 0)
                approval_item_id_str = final_state.get("approval_item_id")
                error = final_state.get("error")
                signals = final_state.get("signals_retrieved", [])

                signal_counts: dict[str, int] = {}
                for signal in signals:
                    src = signal.get("source", "unknown")
                    signal_counts[src] = signal_counts.get(src, 0) + 1

                final_status = "complete" if not error else "failed"

                await run_repo.update_status(
                    run_id=run_id,
                    tenant_id=tenant_id,
                    status=final_status,
                    cost_tokens=cost_tokens,
                    latency_ms=elapsed_ms,
                    error_detail=error,
                    approval_item_id=(
                        uuid.UUID(approval_item_id_str)
                        if approval_item_id_str
                        else None
                    ),
                    input_signal_counts=signal_counts,
                )
                await session.commit()
                logger.info(
                    "Briefing background task complete: run_id=%s status=%s",
                    run_id,
                    final_status,
                )

            except Exception as agent_err:
                elapsed_ms = int((time.monotonic() - start_time) * 1000)
                logger.error(
                    "Briefing agent failed: run_id=%s error=%s", run_id, agent_err
                )
                try:
                    await run_repo.update_status(
                        run_id=run_id,
                        tenant_id=tenant_id,
                        status="failed",
                        latency_ms=elapsed_ms,
                        error_detail=str(agent_err),
                    )
                    await session.commit()
                except Exception:
                    pass

    except Exception as e:
        logger.error("Briefing background task crashed: run_id=%s error=%s", run_id, e)


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


# ── POST /briefing/generate ───────────────────────────────────────────────────


@router.post("/generate", response_model=BriefingRunStatus, status_code=202)
async def generate_briefing(
    background_tasks: BackgroundTasks,
    body: BriefingGenerateRequest | None = None,
    tenant: TenantContext = Depends(get_current_tenant),
) -> BriefingRunStatus:
    """Trigger weekly briefing generation for the current tenant.

    Validates that no briefing is currently running (409 if active run found),
    validates that at least one ingest record exists (400 if no data), then
    creates a BriefingRun record and fires the workflow as a background task.

    Args:
        background_tasks: FastAPI background task queue.
        body: Optional request body with window_days and trigger_type.
        tenant: Authenticated tenant context.

    Returns:
        202 Accepted with BriefingRunStatus (status=generating).

    Raises:
        HTTPException(409): If a briefing is already generating.
        HTTPException(400): If no ingested data exists.
    """
    req = body or BriefingGenerateRequest()
    trace_id = get_current_trace_id()

    factory = get_session_factory()
    async with factory() as session:
        run_repo = BriefingRunRepository(session)

        # 1. Check for active run (prevent concurrent generation)
        active_run = await run_repo.get_active_for_tenant(tenant.tenant_id)
        if active_run:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "briefing_already_running",
                    "message": (
                        f"A briefing is already generating for this tenant "
                        f"(run_id={active_run.id}). "
                        "Poll /briefing/status/{run_id} to check progress."
                    ),
                    "run_id": str(active_run.id),
                },
            )

        # 2. Validate that ingested data exists (check sync_checkpoints)
        from context_os.relational.repositories import CheckpointRepository

        ckpt_repo = CheckpointRepository(session)
        has_data = False
        for integration in ("github", "jira", "slack"):
            ckpt = await ckpt_repo.get(
                tenant_id=tenant.db_tenant_id,
                integration=integration,
                object_type="all",
            )
            if ckpt and ckpt.cursor_value:
                has_data = True
                break

        if not has_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "no_data",
                    "message": (
                        "No ingested data found for this tenant. "
                        "Run POST /ingest/{integration} first."
                    ),
                },
            )

        # 3. Create BriefingRun in generating state
        from datetime import UTC, datetime, timedelta

        now = datetime.now(UTC)
        window_end = now
        window_start = now - timedelta(days=req.window_days)

        run = await run_repo.create(
            tenant_id=tenant.tenant_id,
            trigger_type=req.trigger_type,
            window_days=req.window_days,
            window_start=window_start,
            window_end=window_end,
        )
        await session.commit()
        run_id = run.id

    # 4. Enqueue background task
    background_tasks.add_task(
        _run_briefing_background,
        tenant_id=tenant.tenant_id,
        db_tenant_id=str(tenant.db_tenant_id),
        run_id=run_id,
        window_days=req.window_days,
        trigger_type=req.trigger_type,
    )

    logger.info(
        "Briefing generation enqueued: run_id=%s tenant=%s window_days=%d",
        run_id,
        tenant.tenant_id,
        req.window_days,
    )

    return BriefingRunStatus(
        run_id=str(run_id),
        status="generating",
        tenant_id=tenant.tenant_id,
        window_start=window_start.isoformat() + "Z",
        window_end=window_end.isoformat() + "Z",
        trace_id=trace_id,
    )


# ── GET /briefing/status/{run_id} ─────────────────────────────────────────────


@router.get("/status/{run_id}", response_model=BriefingRunStatus)
async def get_briefing_status(
    run_id: uuid.UUID,
    tenant: TenantContext = Depends(get_current_tenant),
) -> BriefingRunStatus:
    """Get the status of a briefing run.

    Args:
        run_id: UUID of the BriefingRun.
        tenant: Authenticated tenant context.

    Returns:
        BriefingRunStatus with current status and approval_item_id when complete.

    Raises:
        HTTPException(404): If run not found for this tenant.
    """
    factory = get_session_factory()
    async with factory() as session:
        repo = BriefingRunRepository(session)
        run = await repo.get_by_id(run_id, tenant.tenant_id)

    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "not_found",
                "message": f"BriefingRun {run_id} not found",
            },
        )

    return BriefingRunStatus(
        run_id=str(run.id),
        status=run.status,
        tenant_id=run.tenant_id,
        approval_item_id=(str(run.approval_item_id) if run.approval_item_id else None),
        cost_tokens=run.cost_tokens,
        latency_ms=run.latency_ms,
        error=run.error_detail,
        window_start=(run.window_start.isoformat() if run.window_start else None),
        window_end=(run.window_end.isoformat() if run.window_end else None),
    )
