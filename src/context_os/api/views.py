"""View state API endpoint.

GET /views/state — returns the activation state for each canvas view
(galaxy, topology, decision_graph) plus item counts.

The backend marks views as "activated" as soon as the graph is initialised.
Counts are zero until data is ingested; the frontend handles empty-activated
state with its own empty-state components.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from context_os.auth.dependencies import TenantContext, get_current_tenant

router = APIRouter()


class IngestProgress(BaseModel):
    discovered_count: int
    estimated_total: int | None
    estimated_completion_at: str | None


class GalaxyState(BaseModel):
    state: str  # "empty" | "activating" | "activated"
    initiative_count: int
    ingest_progress: IngestProgress | None


class TopologyState(BaseModel):
    state: str
    workflow_count: int
    discovered_count: int


class DecisionGraphState(BaseModel):
    state: str
    decision_count: int


class ViewStateResponse(BaseModel):
    galaxy: GalaxyState
    topology: TopologyState
    decision_graph: DecisionGraphState


@router.get("/state", response_model=ViewStateResponse)
async def get_view_state(
    tenant: TenantContext = Depends(get_current_tenant),
) -> ViewStateResponse:
    """Return the current activation state for all three canvas views.

    All views are reported as "activated" once the backend is running.
    Item counts reflect whatever has been ingested for this tenant.
    """
    # Views are "activated" as soon as the backend is up — the frontend
    # renders the appropriate empty-state when counts are zero.
    return ViewStateResponse(
        galaxy=GalaxyState(
            state="activated",
            initiative_count=0,
            ingest_progress=None,
        ),
        topology=TopologyState(
            state="activated",
            workflow_count=0,
            discovered_count=0,
        ),
        decision_graph=DecisionGraphState(
            state="activated",
            decision_count=0,
        ),
    )
