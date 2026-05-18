"""Graph traversal API endpoint.

POST /graph/traverse — 1-hop or k-hop graph traversal from a starting node

All routes require Clerk JWT authentication via get_current_tenant dependency.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from context_os.auth.dependencies import TenantContext, get_current_tenant
from context_os.core.errors import GraphQueryError, TenantIsolationError
from context_os.graph.client import get_age_pool
from context_os.graph.queries import traverse
from context_os.observability.schema import (
    EVENT,
    StructuredLogRecord,
    emit_structured_log,
)
from context_os.observability.tracer import get_current_trace_id, get_tracer

logger = logging.getLogger(__name__)
router = APIRouter()
_tracer = None


def _get_tracer() -> Any:
    global _tracer
    if _tracer is None:
        try:
            _tracer = get_tracer("context_os.api.graph")
        except RuntimeError:
            pass
    return _tracer


class TraverseRequest(BaseModel):
    """Request body for graph traversal."""

    from_id: str = Field(..., description="Starting node UUID")
    edge_types: list[str] | None = Field(
        default=None,
        description="Filter to these edge labels; empty/None = all",
    )
    max_hops: int = Field(
        default=1,
        ge=1,
        le=5,
        description="Maximum traversal depth (1–5)",
    )
    node_types: list[str] | None = Field(
        default=None,
        description="Filter returned nodes to these types; empty/None = all",
    )


class ProvenanceResponse(BaseModel):
    """Node provenance."""

    source: str
    source_id: str
    fetch_ts: str


class GraphNodeResponse(BaseModel):
    """Graph node in traversal response."""

    id: str
    type: str
    tenant_id: str
    provenance: ProvenanceResponse
    properties: dict[str, Any]


class GraphEdgeResponse(BaseModel):
    """Graph edge in traversal response."""

    id: str
    type: str
    from_id: str
    to_id: str
    properties: dict[str, Any] = Field(default_factory=dict)


class TraversalResponse(BaseModel):
    """Graph traversal result."""

    nodes: list[GraphNodeResponse]
    edges: list[GraphEdgeResponse]
    query_ms: float


def _props_to_node_response(props: dict[str, Any]) -> GraphNodeResponse:
    """Convert raw AGE node properties to GraphNodeResponse."""
    provenance = ProvenanceResponse(
        source=str(props.get("source", "internal")),
        source_id=str(props.get("source_id", "")),
        fetch_ts=str(props.get("fetch_ts", "")),
    )

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
    properties = {k: v for k, v in props.items() if k not in base_fields}

    return GraphNodeResponse(
        id=str(props.get("id", "")),
        type=str(props.get("node_type", "Unknown")),
        tenant_id=str(props.get("tenant_id", "")),
        provenance=provenance,
        properties=properties,
    )


def _edge_to_response(edge_data: dict[str, Any]) -> GraphEdgeResponse:
    """Convert raw AGE edge data to GraphEdgeResponse."""
    edge_id = str(edge_data.get("id", edge_data.get("start_id", "")))
    edge_type = str(edge_data.get("label", edge_data.get("type", "UNKNOWN")))
    from_id = str(edge_data.get("start_id", edge_data.get("from_id", "")))
    to_id = str(edge_data.get("end_id", edge_data.get("to_id", "")))

    base_fields = {"id", "label", "type", "start_id", "end_id", "from_id", "to_id"}
    properties = edge_data.get("properties", {})
    if isinstance(properties, dict):
        extra = {
            k: v
            for k, v in edge_data.items()
            if k not in base_fields and k != "properties"
        }
        properties = {**properties, **extra}

    return GraphEdgeResponse(
        id=edge_id,
        type=edge_type,
        from_id=from_id,
        to_id=to_id,
        properties=properties,
    )


@router.post("/traverse", response_model=TraversalResponse)
async def traverse_graph(
    request: TraverseRequest,
    tenant: TenantContext = Depends(get_current_tenant),
) -> TraversalResponse:
    """1-hop or k-hop graph traversal from a starting node.

    Args:
        request: Traversal parameters (from_id, edge_types, max_hops, node_types).
        tenant: Authenticated tenant context.

    Returns:
        TraversalResponse with nodes, edges, and query timing.

    Raises:
        HTTPException(400): If max_hops > 5 or from_id is invalid.
        HTTPException(500): If the graph query fails.
    """
    tracer = _get_tracer()
    trace_id = get_current_trace_id()
    start_time = time.monotonic()

    if request.max_hops > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "validation_error",
                "message": "max_hops must be ≤ 5",
                "trace_id": trace_id,
            },
        )

    span_ctx = tracer.start_as_current_span("graph.traverse") if tracer else None

    try:
        if span_ctx:
            span = span_ctx.__enter__()  # type: ignore[attr-defined]
            span.set_attribute("context_os.agent_identity", "graph-query-v1")  # type: ignore[attr-defined]
            span.set_attribute("context_os.autonomy_level", 2)  # type: ignore[attr-defined]
            span.set_attribute("context_os.tenant_id", tenant.tenant_id)  # type: ignore[attr-defined]
            span.set_attribute(  # type: ignore[attr-defined]
                "context_os.input_summary",
                (
                    f"from_id={request.from_id} max_hops={request.max_hops}"
                    f" edge_types={request.edge_types}"
                ),
            )
            span.set_attribute("context_os.governance_markers", "{}")  # type: ignore[attr-defined]
            span.set_attribute("gen_ai.system", "context-os")  # type: ignore[attr-defined]
            span.set_attribute("gen_ai.operation.name", "graph_traverse")  # type: ignore[attr-defined]

        pool = get_age_pool()
        result = await traverse(
            pool=pool,
            tenant_id=tenant.tenant_id,
            from_id=request.from_id,
            max_hops=request.max_hops,
            edge_types=request.edge_types,
            node_types=request.node_types,
        )

        if span_ctx and tracer:
            try:
                span.set_attribute(  # type: ignore[attr-defined]
                    "context_os.output_summary",
                    (
                        f"nodes_returned={len(result.nodes)}"
                        f" edges_returned={len(result.edges)}"
                        f" query_ms={result.query_ms:.1f}"
                    ),
                )
            except Exception:
                pass

        duration_ms = (time.monotonic() - start_time) * 1000
        emit_structured_log(
            StructuredLogRecord(
                event=EVENT.GRAPH_TRAVERSE_EXECUTED,
                message=f"Graph traversal executed from {request.from_id}",
                agent_identity="graph-query-v1",
                autonomy_level=2,
                tenant_id=tenant.tenant_id,
                duration_ms=duration_ms,
                trace_id=trace_id,
                metadata={
                    "from_node_id": request.from_id,
                    "max_hops": request.max_hops,
                    "edge_types": request.edge_types,
                    "nodes_returned": len(result.nodes),
                    "edges_returned": len(result.edges),
                },
            )
        )

        nodes_response = []
        for props in result.nodes:
            try:
                nodes_response.append(_props_to_node_response(props))
            except Exception as e:
                logger.warning("Failed to serialize node: %s", e)

        edges_response = []
        for edge_data in result.edges:
            try:
                edges_response.append(_edge_to_response(edge_data))
            except Exception as e:
                logger.warning("Failed to serialize edge: %s", e)

        return TraversalResponse(
            nodes=nodes_response,
            edges=edges_response,
            query_ms=result.query_ms,
        )

    except (GraphQueryError, TenantIsolationError) as e:
        duration_ms = (time.monotonic() - start_time) * 1000
        emit_structured_log(
            StructuredLogRecord(
                event=EVENT.GRAPH_TRAVERSE_ERROR,
                message=f"Graph traversal failed: {e.message}",
                agent_identity="graph-query-v1",
                autonomy_level=2,
                tenant_id=tenant.tenant_id,
                duration_ms=duration_ms,
                level="ERROR",
                trace_id=trace_id,
                metadata={"from_node_id": request.from_id, "error": str(e)},
            )
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.to_dict(),
        ) from e

    except HTTPException:
        raise

    except Exception as e:
        duration_ms = (time.monotonic() - start_time) * 1000
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "graph_query_error",
                "message": str(e),
                "trace_id": trace_id,
            },
        ) from e

    finally:
        if span_ctx:
            try:
                span_ctx.__exit__(None, None, None)  # type: ignore[attr-defined]
            except Exception:
                pass
