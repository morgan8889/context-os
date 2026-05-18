"""Eval API endpoints.

POST /eval/run            — trigger an eval run (returns 202)
GET  /eval/runs           — paginated list of EvalRun records for the tenant
GET  /eval/runs/{run_id}  — full EvalRunResult for a specific run

All routes require Clerk JWT authentication via get_current_tenant dependency.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, cast

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from pydantic import BaseModel

from context_os.auth.dependencies import TenantContext, get_current_tenant
from context_os.db.engine import get_session_factory
from context_os.observability.tracer import get_current_trace_id, get_tracer
from context_os.relational.repositories import (
    EvalRunRepository,
    GoldenDatasetRepository,
)

logger = logging.getLogger(__name__)
router = APIRouter()
_tracer = None


def _get_tracer() -> Any:
    global _tracer
    if _tracer is None:
        try:
            _tracer = get_tracer("context_os.api.eval")
        except RuntimeError:
            pass
    return _tracer


# ── Response schemas ──────────────────────────────────────────────────────────


class EvalRunRequest(BaseModel):
    """Request body for POST /eval/run."""

    eval_type: str  # "synthesizer" | "mapper"
    dataset_id: str | None = None
    compare_to_run_id: str | None = None


class EvalRunSummary(BaseModel):
    """Summary of an EvalRun for list responses."""

    run_id: str
    tenant_id: str
    eval_type: str
    status: str
    gates_passed: bool | None = None
    scores: dict[str, float] = {}
    dataset_version: str | None = None
    duration_ms: int | None = None
    created_at: str


class EvalRunDetail(BaseModel):
    """Full detail for an EvalRun."""

    run_id: str
    tenant_id: str
    eval_type: str
    status: str
    gates_passed: bool | None = None
    scores: dict[str, float] = {}
    score_deltas: dict[str, float] = {}
    dataset_id: str | None = None
    dataset_version: str | None = None
    compared_to_run_id: str | None = None
    duration_ms: int | None = None
    error_detail: str | None = None
    created_at: str
    completed_at: str | None = None


class EvalRunsListResponse(BaseModel):
    """Response schema for GET /eval/runs."""

    runs: list[EvalRunSummary]
    total: int


class EvalRunResponse(BaseModel):
    """Response schema for POST /eval/run (202 Accepted)."""

    run_id: str
    eval_type: str
    tenant_id: str
    status: str
    trace_id: str | None = None


# ── Background task ───────────────────────────────────────────────────────────


async def _run_eval_background(
    tenant_id: str,
    eval_type: str,
    run_id: uuid.UUID,
    dataset_id: str | None,
    compare_to_run_id: str | None,
) -> None:
    """Background task: run the eval suite and update the EvalRun record.

    Args:
        tenant_id: Clerk org ID.
        eval_type: "synthesizer" | "mapper".
        run_id: Pre-created EvalRun UUID to update on completion.
        dataset_id: Golden dataset UUID (or None to use latest).
        compare_to_run_id: Prior run UUID for delta comparison.
    """
    try:
        from context_os.core.errors import EvalError
        from context_os.eval.golden_dataset import load_dataset
        from context_os.eval.mapper_eval import MapperEvalRunner
        from context_os.eval.synthesizer_eval import SynthesizerEvalRunner

        factory = get_session_factory()
        async with factory() as session:
            eval_repo = EvalRunRepository(session)
            golden_repo = GoldenDatasetRepository(session)

            try:
                dataset = await load_dataset(
                    eval_type=eval_type,
                    version="latest",
                    repo=golden_repo,
                )
            except ValueError as exc:
                await eval_repo.update_scores(
                    run_id=run_id,
                    tenant_id=tenant_id,
                    status="failed",
                    scores={},
                    gates_passed=False,
                    score_deltas={},
                    error_detail=str(exc),
                )
                await session.commit()
                return

            if eval_type == "synthesizer":
                runner: SynthesizerEvalRunner | MapperEvalRunner = (
                    SynthesizerEvalRunner(tenant_id=tenant_id)
                )
            else:
                runner = MapperEvalRunner(tenant_id=tenant_id)

            try:
                result = await runner.run(
                    dataset=dataset,
                    session=session,
                    compare_to_run_id=compare_to_run_id,
                )
                gates_passed = result.gates_passed
                error_detail = None
            except EvalError as exc:
                gates_passed = False
                error_detail = exc.message
                result = None  # type: ignore[assignment]

            # Update the pre-created EvalRun with results
            await eval_repo.update_scores(
                run_id=run_id,
                tenant_id=tenant_id,
                status="complete",
                scores=result.scores if result else {},
                gates_passed=gates_passed,
                score_deltas={
                    k: v
                    for k, v in (result.score_deltas if result else {}).items()
                    if v is not None
                },
                error_detail=error_detail,
            )
            await session.commit()

            logger.info(
                "Eval background run complete: run_id=%s eval_type=%s gates=%s",
                run_id,
                eval_type,
                gates_passed,
            )

    except Exception as exc:
        logger.error("Eval background run crashed: run_id=%s error=%s", run_id, exc)


# ── POST /eval/run ────────────────────────────────────────────────────────────


@router.post("/run", response_model=EvalRunResponse, status_code=202)
async def trigger_eval_run(
    background_tasks: BackgroundTasks,
    body: EvalRunRequest,
    tenant: TenantContext = Depends(get_current_tenant),
) -> EvalRunResponse:
    """Trigger an eval run for the current tenant.

    Creates an EvalRun record in 'running' status and fires the eval suite
    as a background task.

    Args:
        background_tasks: FastAPI background task queue.
        body: Request body with eval_type and optional dataset_id.
        tenant: Authenticated tenant context.

    Returns:
        202 Accepted with EvalRunResponse.

    Raises:
        HTTPException(400): If eval_type is not recognized.
    """
    if body.eval_type not in ("synthesizer", "mapper"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "invalid_eval_type",
                "message": (
                    f"eval_type must be 'synthesizer' or 'mapper', "
                    f"got {body.eval_type!r}"
                ),
            },
        )

    trace_id = get_current_trace_id()

    factory = get_session_factory()
    async with factory() as session:
        repo = EvalRunRepository(session)
        run = await repo.create(
            tenant_id=tenant.tenant_id,
            eval_type=body.eval_type,
            dataset_id=uuid.UUID(body.dataset_id) if body.dataset_id else None,
            dataset_version="latest",
            status="running",
        )
        await session.commit()
        run_id = run.id

    background_tasks.add_task(
        _run_eval_background,
        tenant_id=tenant.tenant_id,
        eval_type=body.eval_type,
        run_id=run_id,
        dataset_id=body.dataset_id,
        compare_to_run_id=body.compare_to_run_id,
    )

    logger.info(
        "Eval run enqueued: run_id=%s eval_type=%s tenant=%s",
        run_id,
        body.eval_type,
        tenant.tenant_id,
    )

    return EvalRunResponse(
        run_id=str(run_id),
        eval_type=body.eval_type,
        tenant_id=tenant.tenant_id,
        status="running",
        trace_id=trace_id,
    )


# ── GET /eval/runs ────────────────────────────────────────────────────────────


@router.get("/runs", response_model=EvalRunsListResponse)
async def list_eval_runs(
    eval_type: str | None = Query(
        default=None, description="Filter by eval_type: synthesizer | mapper"
    ),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    tenant: TenantContext = Depends(get_current_tenant),
) -> EvalRunsListResponse:
    """List EvalRun records for the current tenant.

    Args:
        eval_type: Optional filter by eval type.
        limit: Max runs to return.
        offset: Pagination offset.
        tenant: Authenticated tenant context.

    Returns:
        EvalRunsListResponse with paginated run summaries.
    """
    factory = get_session_factory()
    async with factory() as session:
        repo = EvalRunRepository(session)
        runs = await repo.list_by_tenant(
            tenant_id=tenant.tenant_id,
            eval_type=eval_type,
            limit=limit,
            offset=offset,
        )

    summaries = [
        EvalRunSummary(
            run_id=str(run.id),
            tenant_id=run.tenant_id,
            eval_type=run.eval_type,
            status=run.status,
            gates_passed=run.gates_passed,
            scores=cast(dict[str, float], run.scores or {}),
            dataset_version=run.dataset_version,
            duration_ms=run.duration_ms,
            created_at=run.created_at.isoformat(),
        )
        for run in runs
    ]

    return EvalRunsListResponse(runs=summaries, total=len(summaries))


# ── GET /eval/runs/{run_id} ───────────────────────────────────────────────────


@router.get("/runs/{run_id}", response_model=EvalRunDetail)
async def get_eval_run(
    run_id: uuid.UUID,
    tenant: TenantContext = Depends(get_current_tenant),
) -> EvalRunDetail:
    """Get full detail for a specific EvalRun.

    Args:
        run_id: UUID of the EvalRun.
        tenant: Authenticated tenant context.

    Returns:
        EvalRunDetail with scores, gates_passed, and score_deltas.

    Raises:
        HTTPException(404): If run not found for this tenant.
    """
    factory = get_session_factory()
    async with factory() as session:
        repo = EvalRunRepository(session)
        run = await repo.get_by_id(run_id, tenant.tenant_id)

    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "not_found",
                "message": f"EvalRun {run_id} not found",
            },
        )

    return EvalRunDetail(
        run_id=str(run.id),
        tenant_id=run.tenant_id,
        eval_type=run.eval_type,
        status=run.status,
        gates_passed=run.gates_passed,
        scores=cast(dict[str, float], run.scores or {}),
        score_deltas=cast(dict[str, float], run.score_deltas or {}),
        dataset_id=str(run.dataset_id) if run.dataset_id else None,
        dataset_version=run.dataset_version,
        compared_to_run_id=(
            str(run.compared_to_run_id) if run.compared_to_run_id else None
        ),
        duration_ms=run.duration_ms,
        error_detail=run.error_detail,
        created_at=run.created_at.isoformat(),
        completed_at=run.completed_at.isoformat() if run.completed_at else None,
    )
