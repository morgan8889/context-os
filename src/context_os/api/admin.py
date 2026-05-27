"""Admin API endpoints for entity inspection and onboarding funnel analytics.

GET /admin/entities           — list all normalized entities for the tenant
GET /admin/funnel             — onboarding funnel report (Platform Operator only)
GET /admin/survey-responses   — raw survey answers (Platform Operator only)

Protected routes use require_platform_operator().
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select, text

from context_os.api.admin_funnel import build_funnel_rows
from context_os.auth.dependencies import (
    TenantContext,
    require_platform_operator,
)
from context_os.db.engine import get_session_factory
from context_os.db.models import ActivationEvent, OnboardingSession, Tenant
from context_os.graph.client import get_age_pool
from context_os.graph.mutations import get_nodes_for_tenant

logger = logging.getLogger(__name__)
router = APIRouter()


class Provenance(BaseModel):
    """Node provenance information."""

    source: str
    source_id: str
    fetch_ts: str


class GraphNodeResponse(BaseModel):
    """Response schema for a single graph node."""

    id: str
    type: str
    tenant_id: str
    provenance: Provenance
    properties: dict[str, Any]


class EntitiesResponse(BaseModel):
    """Paginated entity list response."""

    items: list[GraphNodeResponse]
    total: int
    limit: int
    offset: int


def _node_to_response(node_props: dict[str, Any]) -> GraphNodeResponse:
    """Convert raw AGE node properties to GraphNodeResponse.

    Args:
        node_props: Raw properties dict from AGE graph node.

    Returns:
        GraphNodeResponse with provenance extracted.
    """
    node_id = str(node_props.get("id", ""))
    node_type = str(node_props.get("node_type", node_props.get("label", "Unknown")))
    tenant_id = str(node_props.get("tenant_id", ""))

    provenance = Provenance(
        source=str(node_props.get("source", "internal")),
        source_id=str(node_props.get("source_id", "")),
        fetch_ts=str(node_props.get("fetch_ts", "")),
    )

    # Properties dict excludes base fields for cleaner output
    base_fields = {
        "id",
        "tenant_id",
        "source",
        "source_id",
        "fetch_ts",
        "created_at",
        "updated_at",
        "node_type",
    }
    properties = {k: v for k, v in node_props.items() if k not in base_fields}

    return GraphNodeResponse(
        id=node_id,
        type=node_type,
        tenant_id=tenant_id,
        provenance=provenance,
        properties=properties,
    )


@router.get("/entities", response_model=EntitiesResponse)
async def list_entities(
    type: str | None = Query(default=None, description="Filter by node type"),
    source: str | None = Query(default=None, description="Filter by source"),
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum results"),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
    tenant: TenantContext = Depends(require_platform_operator),
) -> EntitiesResponse:
    """List all normalized entities for the authenticated tenant.

    Queries the AGE graph with optional type and source filters.
    Returns paginated results with provenance information.

    Args:
        type: Optional node type filter (Goal, Initiative, Signal, etc.).
        source: Optional source filter (github, jira, slack, internal).
        limit: Maximum number of results (default 100, max 1000).
        offset: Pagination offset.
        tenant: Authenticated tenant context.

    Returns:
        Paginated list of graph nodes with provenance.
    """
    pool = get_age_pool()

    try:
        nodes_data, total = await get_nodes_for_tenant(
            pool=pool,
            tenant_id=tenant.tenant_id,
            node_type=type,
            source=source,
            limit=limit,
            offset=offset,
        )
    except Exception as e:
        logger.error("Failed to query entities for tenant %s: %s", tenant.tenant_id, e)
        raise

    items = []
    for node_props in nodes_data:
        try:
            items.append(_node_to_response(node_props))
        except Exception as e:
            logger.warning("Failed to serialize node: %s — %s", node_props, e)

    return EntitiesResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


# ── Phase 4: Admin funnel + survey-responses ───────────────────────────────────


class AdminFunnelRowResponse(BaseModel):
    """Response schema for a single funnel row."""

    tenant_id: str
    tenant_name: str
    current_step: str
    drop_off_flag: bool
    signup_to_connect_ms: int | None
    connect_to_ingest_ms: int | None
    ingest_to_briefing_ms: int | None
    total_active_attention_ms: int | None


class AdminFunnelResponse(BaseModel):
    """Response schema for GET /admin/funnel."""

    rows: list[AdminFunnelRowResponse]


class SurveyResponseRow(BaseModel):
    """Single survey response row for GET /admin/survey-responses."""

    tenant_id: str
    tenant_name: str
    option: str | None
    free_text: str | None
    answered_at: str | None


class SurveyResponsesResponse(BaseModel):
    """Response schema for GET /admin/survey-responses."""

    responses: list[SurveyResponseRow]


@router.get(
    "/funnel",
    response_model=AdminFunnelResponse,
    tags=["Admin"],
)
async def get_onboarding_funnel(
    _ctx: TenantContext = Depends(require_platform_operator),
) -> AdminFunnelResponse:
    """Return the onboarding funnel report across all tenants.

    Joins onboarding_sessions with tenants and optionally activation_events
    to compute drop-off flags and timing segments.

    Args:
        _ctx: Platform Operator context (enforced by dependency).

    Returns:
        AdminFunnelResponse with one row per org.
    """
    factory = get_session_factory()
    async with factory() as db:
        # Join onboarding_sessions + tenants + LEFT JOIN activation_events
        stmt = (
            select(
                OnboardingSession.tenant_id,
                Tenant.name.label("tenant_name"),
                OnboardingSession.current_step,
                OnboardingSession.updated_at,
                OnboardingSession.step_started_at,
                OnboardingSession.step_completed_at,
                ActivationEvent.signup_to_connect_ms,
                ActivationEvent.connect_to_ingest_ms,
                ActivationEvent.ingest_to_briefing_ms,
                ActivationEvent.total_active_attention_ms,
            )
            .join(Tenant, Tenant.id == OnboardingSession.tenant_id)
            .outerjoin(
                ActivationEvent,
                ActivationEvent.tenant_id == OnboardingSession.tenant_id,
            )
        )
        result = await db.execute(stmt)
        raw_rows = result.all()

    funnel_rows = build_funnel_rows(list(raw_rows))

    rows = [
        AdminFunnelRowResponse(
            tenant_id=str(r.tenant_id),
            tenant_name=r.tenant_name,
            current_step=r.current_step,
            drop_off_flag=r.drop_off_flag,
            signup_to_connect_ms=r.signup_to_connect_ms,
            connect_to_ingest_ms=r.connect_to_ingest_ms,
            ingest_to_briefing_ms=r.ingest_to_briefing_ms,
            total_active_attention_ms=r.total_active_attention_ms,
        )
        for r in funnel_rows
    ]
    return AdminFunnelResponse(rows=rows)


@router.get(
    "/survey-responses",
    response_model=SurveyResponsesResponse,
    tags=["Admin"],
)
async def get_survey_responses(
    _ctx: TenantContext = Depends(require_platform_operator),
) -> SurveyResponsesResponse:
    """Return all survey answers ordered by answered_at DESC.

    Args:
        _ctx: Platform Operator context (enforced by dependency).

    Returns:
        SurveyResponsesResponse with one row per org that answered.
    """
    factory = get_session_factory()
    async with factory() as db:
        stmt = (
            select(
                OnboardingSession.tenant_id,
                Tenant.name.label("tenant_name"),
                OnboardingSession.survey_answer,
                OnboardingSession.step_completed_at,
            )
            .join(Tenant, Tenant.id == OnboardingSession.tenant_id)
            .where(OnboardingSession.survey_answer.isnot(None))
            .order_by(
                text(
                    "(onboarding_sessions.step_completed_at->>'survey') DESC NULLS LAST"
                )
            )
        )
        result = await db.execute(stmt)
        raw_rows = result.all()

    responses: list[SurveyResponseRow] = []
    for row in raw_rows:
        survey = row.survey_answer or {}
        completed_at = (row.step_completed_at or {}).get("survey")
        responses.append(
            SurveyResponseRow(
                tenant_id=str(row.tenant_id),
                tenant_name=row.tenant_name,
                option=survey.get("option"),
                free_text=survey.get("free_text"),
                answered_at=completed_at,
            )
        )

    return SurveyResponsesResponse(responses=responses)
