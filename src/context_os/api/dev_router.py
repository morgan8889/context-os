"""Development-only router: in-memory seed store + frontend view endpoints.

Mounted at /api/v1 when the server starts. Provides all the read/write
endpoints the Phase 3 frontend needs for local dev and visual testing.
DO NOT deploy to production — gated by DEV_SEED_ENABLED env var.

Seed endpoints (called by web/scripts/seed-*.ts):
  POST /api/v1/graph/nodes/seed
  POST /api/v1/graph/edges/seed
  POST /api/v1/graph/seed          (workflows)
  POST /api/v1/dev/seed-decisions

View endpoints (called by frontend data hooks):
  GET  /api/v1/graph/nodes
  GET  /api/v1/graph/edges
  GET  /api/v1/graph/snapshots
  GET  /api/v1/workflows
  GET  /api/v1/decisions
  GET  /api/v1/views/state
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()

# ── In-memory store ────────────────────────────────────────────────────────

_nodes: list[dict[str, Any]] = []
_edges: list[dict[str, Any]] = []
_workflows: list[dict[str, Any]] = []
_decisions: list[dict[str, Any]] = []
_decision_edges: list[dict[str, Any]] = []

# ── Request/response models ────────────────────────────────────────────────


class NodeSeedRequest(BaseModel):
    nodes: list[dict[str, Any]]


class EdgeSeedRequest(BaseModel):
    edges: list[dict[str, Any]]


class WorkflowSeedRequest(BaseModel):
    workflows: list[dict[str, Any]]
    view_state: str = "activated"


class DecisionSeedRequest(BaseModel):
    decisions: list[dict[str, Any]]
    edges: list[dict[str, Any]] = []
    view_state: str = "activated"


# ── Seed endpoints ─────────────────────────────────────────────────────────


@router.post("/graph/nodes/seed")
async def seed_nodes(body: NodeSeedRequest) -> dict[str, int]:
    global _nodes
    _nodes = body.nodes
    logger.info("Dev seed: stored %d nodes", len(_nodes))
    return {"count": len(_nodes)}


@router.post("/graph/edges/seed")
async def seed_edges(body: EdgeSeedRequest) -> dict[str, int]:
    global _edges
    _edges = body.edges
    logger.info("Dev seed: stored %d edges", len(_edges))
    return {"count": len(_edges)}


@router.post("/graph/seed")
async def seed_workflows(body: WorkflowSeedRequest) -> dict[str, int]:
    global _workflows
    _workflows = body.workflows
    logger.info("Dev seed: stored %d workflows", len(_workflows))
    return {"count": len(_workflows)}


@router.post("/dev/seed-decisions")
async def seed_decisions(body: DecisionSeedRequest) -> dict[str, int]:
    global _decisions, _decision_edges
    _decisions = body.decisions
    _decision_edges = body.edges
    logger.info(
        "Dev seed: stored %d decisions, %d decision edges",
        len(_decisions),
        len(_decision_edges),
    )
    return {"decisions": len(_decisions), "edges": len(_decision_edges)}


# ── View endpoints ─────────────────────────────────────────────────────────


@router.get("/graph/nodes")
async def get_nodes(
    cursor: str | None = Query(None),
    limit: int = Query(100),
) -> dict[str, Any]:
    start = 0
    if cursor:
        try:
            start = int(cursor)
        except ValueError:
            start = 0
    page = _nodes[start : start + limit]
    next_cursor = str(start + limit) if start + limit < len(_nodes) else None
    return {"items": page, "next_cursor": next_cursor, "total": len(_nodes)}


@router.get("/graph/edges")
async def get_edges(
    cursor: str | None = Query(None),
    limit: int = Query(500),
) -> dict[str, Any]:
    start = 0
    if cursor:
        try:
            start = int(cursor)
        except ValueError:
            start = 0
    page = _edges[start : start + limit]
    next_cursor = str(start + limit) if start + limit < len(_edges) else None
    return {"items": page, "next_cursor": next_cursor, "total": len(_edges)}


@router.get("/graph/snapshots")
async def get_snapshots() -> list[dict[str, Any]]:
    return []


@router.get("/workflows")
async def get_workflows() -> list[dict[str, Any]]:
    return _workflows


@router.get("/decisions")
async def get_decisions(
    q: str | None = Query(None),
    status: str | None = Query(None),
) -> dict[str, Any]:
    items = _decisions
    if q:
        q_lower = q.lower()
        items = [
            d
            for d in items
            if q_lower in d.get("title", "").lower()
            or q_lower in d.get("rationale", "").lower()
        ]
    if status:
        items = [d for d in items if d.get("status") == status]
    return {"items": items, "edges": _decision_edges}


@router.get("/views/state")
async def get_views_state() -> dict[str, Any]:
    node_count = len(_nodes)
    workflow_count = len(_workflows)
    decision_count = len(_decisions)

    def _state(count: int) -> str:
        if count == 0:
            return "empty"
        if count < 10:
            return "activating"
        return "activated"

    return {
        "galaxy": {
            "state": _state(node_count),
            "initiative_count": node_count,
            "ingest_progress": None,
        },
        "topology": {
            "state": _state(workflow_count),
            "workflow_count": workflow_count,
            "discovered_count": workflow_count,
        },
        "decision_graph": {
            "state": _state(decision_count),
            "decision_count": decision_count,
        },
    }
