"""Admin API endpoints for entity inspection.

GET /admin/entities — list all normalized entities for the authenticated tenant

All routes require Clerk JWT authentication via get_current_tenant dependency.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from context_os.auth.dependencies import TenantContext, get_current_tenant
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
    tenant: TenantContext = Depends(get_current_tenant),
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
