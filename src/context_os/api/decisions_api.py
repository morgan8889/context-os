"""Decisions API endpoint.

GET /decisions — list architectural decision nodes for the decision graph view.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from context_os.auth.dependencies import TenantContext, get_current_tenant

router = APIRouter()


class DecisionAlternative(BaseModel):
    label: str
    reason: str


class DecisionResponse(BaseModel):
    id: str
    title: str
    rationale: str
    alternatives: list[DecisionAlternative]
    author_id: str | None
    author_name: str | None
    captured_at: str
    impacted_systems: list[str]
    status: str


class DecisionEdgeResponse(BaseModel):
    id: str
    source_id: str
    target_id: str
    edge_type: str


class DecisionsListResponse(BaseModel):
    items: list[DecisionResponse]
    edges: list[DecisionEdgeResponse]


@router.get("", response_model=DecisionsListResponse)
async def list_decisions(
    q: str | None = Query(default=None, description="Keyword search"),
    from_date: str | None = Query(default=None, alias="fromDate"),
    to_date: str | None = Query(default=None, alias="toDate"),
    author_id: str | None = Query(default=None, alias="authorId"),
    impacted_system: str | None = Query(default=None, alias="impactedSystem"),
    tenant: TenantContext = Depends(get_current_tenant),
) -> DecisionsListResponse:
    """List architectural decisions for the decision graph canvas."""
    # Returns empty list until decisions are promoted from briefing approvals.
    return DecisionsListResponse(items=[], edges=[])
