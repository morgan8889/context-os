"""View state API endpoint.

GET /views/state — returns the activation state for each canvas view
(galaxy, topology, decision_graph) plus item counts.

The backend marks views as "activated" as soon as the graph is initialised.
Counts are zero until data is ingested; the frontend handles empty-activated
state with its own empty-state components.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from context_os.auth.dependencies import TenantContext, get_current_tenant

logger = logging.getLogger(__name__)
router = APIRouter()


_ALLOWED_NODE_LABELS = frozenset({"Initiative", "WorkflowStep", "Decision"})


async def _count_age_nodes(tenant_id: str, node_type: str) -> int:
    """Count AGE nodes of a given label for a tenant. Returns 0 on any error."""
    if node_type not in _ALLOWED_NODE_LABELS:
        return 0
    try:
        from context_os.graph.client import get_age_pool, run_cypher

        pool = get_age_pool()
        cypher = (
            f"MATCH (n:{node_type} {{tenant_id: $tenant_id}}) RETURN count(n) AS cnt"  # noqa: S608
        )
        rows = await run_cypher(
            pool,
            cypher,
            {"tenant_id": tenant_id},
            columns=[("cnt", "agtype")],
        )
        return int(rows[0]["cnt"]) if rows else 0
    except Exception:
        return 0


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
    """Return the current activation state for all three canvas views."""
    initiative_count = await _count_age_nodes(tenant.tenant_id, "Initiative")
    galaxy_state = "activated" if initiative_count > 0 else "empty"

    return ViewStateResponse(
        galaxy=GalaxyState(
            state=galaxy_state,
            initiative_count=initiative_count,
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
