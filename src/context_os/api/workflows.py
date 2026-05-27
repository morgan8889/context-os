"""Workflows API endpoint.

GET /workflows — list workflow definitions for the topology view.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from context_os.auth.dependencies import TenantContext, get_current_tenant

router = APIRouter()


class WorkflowStepResponse(BaseModel):
    id: str
    workflow_id: str
    label: str
    step_index: int
    status: str
    owner_team: str | None
    owner_actor: str | None
    autonomy_level: int
    latency_p50_ms: float | None
    latency_p95_ms: float | None


class WorkflowEdgeResponse(BaseModel):
    id: str
    source_id: str
    target_id: str
    label: str | None


class WorkflowResponse(BaseModel):
    id: str
    name: str
    owner_team: str | None
    status: str
    steps: list[WorkflowStepResponse]
    edges: list[WorkflowEdgeResponse]


@router.get("", response_model=list[WorkflowResponse])
async def list_workflows(
    tenant: TenantContext = Depends(get_current_tenant),
) -> list[WorkflowResponse]:
    """List all workflow definitions for the topology canvas."""
    # Returns empty list until workflows are ingested from source systems.
    return []
