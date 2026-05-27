"""Onboarding API: Workflow-First onboarding flow endpoints.

Router prefix: /onboarding

Routes:
    GET  /session           — get or create onboarding session
    POST /survey            — record survey answer, advance to connect
    POST /scope             — select sources, create IngestJob, advance to ingest
    GET  /ingest-status     — current IngestJob status
    POST /activation        — record first-briefing approval, advance to activated
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select

from context_os.auth.dependencies import TenantContext, get_current_tenant
from context_os.db.engine import get_session_factory
from context_os.db.models import ActivationEvent, ApprovalItem, IngestJob
from context_os.services.ingest_service import IngestService
from context_os.services.onboarding_service import (
    InvalidTransitionError,
    OnboardingService,
)

logger = logging.getLogger(__name__)
router = APIRouter()

_SURVEY_OPTIONS = frozenset(
    [
        "briefings",
        "dependencies",
        "decision_retrieval",
        "architecture_review_cycle_time",
        "something_else",
    ]
)


# ── Request / Response schemas ────────────────────────────────────────────────


class SurveyRequest(BaseModel):
    """POST /survey request body."""

    option: str = Field(..., description="Survey answer option (see _SURVEY_OPTIONS)")
    free_text: str | None = Field(
        default=None,
        max_length=500,
        description="Optional free-text elaboration",
    )


class ScopeRequest(BaseModel):
    """POST /scope request body."""

    sources: list[str] = Field(
        ..., min_length=1, description="Integration sources to ingest"
    )


class ActivationRequest(BaseModel):
    """POST /activation request body."""

    briefing_id: str = Field(..., description="UUID of the approved briefing")
    accepted_as_is: bool = Field(
        default=True, description="Whether the briefing was accepted without edits"
    )


def _session_to_dict(session: Any) -> dict[str, Any]:
    """Serialize an OnboardingSession ORM object to a plain dict."""
    return {
        "id": str(session.id),
        "tenant_id": str(session.tenant_id),
        "current_step": session.current_step,
        "survey_answer": session.survey_answer,
        "connected_integrations": session.connected_integrations,
        "scope_selection": session.scope_selection,
        "ingest_job_id": (
            str(session.ingest_job_id) if session.ingest_job_id else None
        ),
        "step_started_at": session.step_started_at,
        "step_completed_at": session.step_completed_at,
        "activated_at": (
            session.activated_at.isoformat() if session.activated_at else None
        ),
        "created_at": session.created_at.isoformat() if session.created_at else None,
        "updated_at": session.updated_at.isoformat() if session.updated_at else None,
    }


def _job_to_dict(job: Any) -> dict[str, Any]:
    """Serialize an IngestJob ORM object to a plain dict."""
    return {
        "id": str(job.id),
        "tenant_id": str(job.tenant_id),
        "source": job.source,
        "status": job.status,
        "progress_pct": job.progress_pct,
        "record_counts": job.record_counts,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "last_record_at": (
            job.last_record_at.isoformat() if job.last_record_at else None
        ),
        "error_detail": job.error_detail,
    }


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.get("/session")
async def get_session(
    ctx: TenantContext = Depends(get_current_tenant),
) -> dict[str, Any]:
    """Get or create the onboarding session for the authenticated tenant.

    Args:
        ctx: Authenticated tenant context.

    Returns:
        OnboardingSession as a dict.
    """
    factory = get_session_factory()
    async with factory() as db:
        svc = OnboardingService(db)
        session = await svc.get_or_create(ctx.db_tenant_id)
        await db.commit()
    return _session_to_dict(session)


@router.post("/survey")
async def post_survey(
    body: SurveyRequest,
    ctx: TenantContext = Depends(get_current_tenant),
) -> dict[str, Any]:
    """Record the survey answer and advance session from survey → connect.

    Args:
        body: SurveyRequest with option and optional free_text.
        ctx: Authenticated tenant context.

    Returns:
        Updated OnboardingSession as a dict.

    Raises:
        HTTPException(400): When option is not in the allowed set.
        HTTPException(409): When the session is already past survey.
    """
    if body.option not in _SURVEY_OPTIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "invalid_option",
                "message": f"option must be one of {sorted(_SURVEY_OPTIONS)}",
            },
        )

    factory = get_session_factory()
    async with factory() as db:
        svc = OnboardingService(db)
        session = await svc.get_or_create(ctx.db_tenant_id)

        data = {"option": body.option, "free_text": body.free_text}
        try:
            session = await svc.advance_step(session.id, "connect", data)  # type: ignore[arg-type]
        except InvalidTransitionError:
            if session.current_step != "survey":
                # Session already past survey — idempotent return
                await db.commit()
                return _session_to_dict(session)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "invalid_transition",
                    "message": "Session cannot advance to connect from current step",
                },
            )

        await db.commit()
    return _session_to_dict(session)


@router.post("/scope")
async def post_scope(
    body: ScopeRequest,
    ctx: TenantContext = Depends(get_current_tenant),
) -> dict[str, Any]:
    """Select integration sources, create IngestJob, advance to ingest.

    Args:
        body: ScopeRequest with list of sources.
        ctx: Authenticated tenant context.

    Returns:
        IngestJob dict.
    """
    factory = get_session_factory()
    async with factory() as db:
        svc = OnboardingService(db)
        session = await svc.get_or_create(ctx.db_tenant_id)

        source = ",".join(body.sources) if len(body.sources) > 1 else body.sources[0]

        ingest_svc = IngestService(db)
        # Idempotent: reuse existing job if scope already submitted
        if session.ingest_job_id is not None:
            job = await ingest_svc.get_job(session.ingest_job_id)
        else:
            job = await ingest_svc.create_job(ctx.db_tenant_id, source)
            session.ingest_job_id = job.id

        scope_data = {"sources": body.sources}
        # Two forward steps: connect → scope → ingest
        for target_step in ("scope", "ingest"):
            try:
                await svc.advance_step(session.id, target_step, scope_data)  # type: ignore[arg-type]
            except InvalidTransitionError:
                pass  # already at or past this step

        await db.commit()
    return _job_to_dict(job)


@router.get("/ingest-status")
async def get_ingest_status(
    ctx: TenantContext = Depends(get_current_tenant),
) -> dict[str, Any]:
    """Return the current IngestJob for the tenant's onboarding session.

    Args:
        ctx: Authenticated tenant context.

    Returns:
        IngestJob dict.

    Raises:
        HTTPException(404): When no ingest job has been started.
    """
    factory = get_session_factory()
    async with factory() as db:
        svc = OnboardingService(db)
        session = await svc.get_or_create(ctx.db_tenant_id)

        if session.ingest_job_id is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "no_ingest_job", "message": "No ingest job started"},
            )

        result = await db.execute(
            select(IngestJob).where(IngestJob.id == session.ingest_job_id)
        )
        job = result.scalar_one_or_none()
        if job is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "job_not_found", "message": "Ingest job not found"},
            )

    return _job_to_dict(job)


@router.post("/activation")
async def post_activation(
    body: ActivationRequest,
    ctx: TenantContext = Depends(get_current_tenant),
) -> dict[str, Any]:
    """Record first-briefing approval; advance session to 'activated'.

    Writes an ActivationEvent with timing segments computed from the session's
    step timestamps.

    Args:
        body: ActivationRequest with briefing_id and accepted_as_is flag.
        ctx: Authenticated tenant context.

    Returns:
        Updated OnboardingSession as a dict.

    Raises:
        HTTPException(404): When the briefing_id is not found.
    """
    try:
        briefing_uuid = uuid.UUID(body.briefing_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "invalid_briefing_id", "message": "Invalid UUID format"},
        )

    factory = get_session_factory()
    async with factory() as db:
        # Validate briefing exists for this tenant
        result = await db.execute(
            select(ApprovalItem).where(
                ApprovalItem.id == briefing_uuid,
                ApprovalItem.tenant_id == ctx.tenant_id,
            )
        )
        briefing = result.scalar_one_or_none()
        if briefing is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "briefing_not_found", "message": "Briefing not found"},
            )

        svc = OnboardingService(db)
        session = await svc.get_or_create(ctx.db_tenant_id)

        # Compute timing segments from step timestamps
        started = session.step_started_at or {}
        completed = session.step_completed_at or {}
        signup_to_connect_ms = _compute_ms(
            started.get("survey"), completed.get("connect")
        )
        connect_to_ingest_ms = _compute_ms(
            completed.get("connect"), completed.get("ingest")
        )
        ingest_to_briefing_ms = _compute_ms(
            completed.get("ingest"), started.get("briefing")
        )
        total_ms = sum(
            v
            for v in [signup_to_connect_ms, connect_to_ingest_ms, ingest_to_briefing_ms]
            if v is not None
        )

        # Create ActivationEvent (upsert: one per tenant)
        event_result = await db.execute(
            select(ActivationEvent).where(ActivationEvent.tenant_id == ctx.db_tenant_id)
        )
        existing_event = event_result.scalar_one_or_none()
        if existing_event is None:
            event = ActivationEvent(
                tenant_id=ctx.db_tenant_id,
                occurred_at=datetime.now(UTC),
                signup_to_connect_ms=signup_to_connect_ms,
                connect_to_ingest_ms=connect_to_ingest_ms,
                ingest_to_briefing_ms=ingest_to_briefing_ms,
                total_active_attention_ms=total_ms if total_ms else None,
                accept_as_is=body.accepted_as_is,
            )
            db.add(event)
            await db.flush()

        # Advance session to activated
        try:
            session = await svc.advance_step(
                session.id,
                "activated",
                {"briefing_id": str(briefing_uuid)},
            )
        except InvalidTransitionError:
            pass  # Already activated — idempotent

        await db.commit()

    return _session_to_dict(session)


def _compute_ms(start_iso: object, end_iso: object) -> int | None:
    """Compute milliseconds between two ISO 8601 timestamp strings.

    Accepts the raw values pulled from JSONB step-timestamp maps (typed as
    ``object``). Returns None if either value is missing or unparseable.

    Args:
        start_iso: ISO 8601 start timestamp.
        end_iso: ISO 8601 end timestamp.

    Returns:
        Duration in milliseconds, or None if either timestamp is missing.
    """
    if not start_iso or not end_iso:
        return None
    try:
        start = datetime.fromisoformat(str(start_iso))
        end = datetime.fromisoformat(str(end_iso))
        return max(0, int((end - start).total_seconds() * 1000))
    except (ValueError, TypeError):
        return None
