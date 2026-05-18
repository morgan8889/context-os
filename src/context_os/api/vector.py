"""Vector search API endpoint.

POST /vector/search — semantic top-k similarity search

All routes require Clerk JWT authentication via get_current_tenant dependency.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from context_os.auth.dependencies import TenantContext, get_current_tenant
from context_os.core.errors import TenantIsolationError, VectorSearchError
from context_os.db.engine import get_session_factory
from context_os.graph.client import get_age_pool
from context_os.observability.schema import (
    EVENT,
    StructuredLogRecord,
    emit_structured_log,
)
from context_os.observability.tracer import get_current_trace_id, get_tracer
from context_os.vector.search import search

logger = logging.getLogger(__name__)
router = APIRouter()
_tracer = None


def _get_tracer() -> Any:
    global _tracer
    if _tracer is None:
        try:
            _tracer = get_tracer("context_os.api.vector")
        except RuntimeError:
            pass
    return _tracer


class VectorSearchRequest(BaseModel):
    """Request body for vector search."""

    query: str = Field(..., description="Natural language query to embed and search")
    k: int = Field(default=5, ge=1, le=50, description="Number of results to return")
    node_types: list[str] = Field(
        default=["Artifact", "Memory"],
        description="Node types to search",
    )


class ProvenanceResponse(BaseModel):
    """Node provenance."""

    source: str
    source_id: str
    fetch_ts: str


class GraphNodeResponse(BaseModel):
    """Graph node in search response."""

    id: str
    type: str
    tenant_id: str
    provenance: ProvenanceResponse
    properties: dict[str, Any]


class SearchResultItem(BaseModel):
    """Single vector search result."""

    node: GraphNodeResponse
    distance: float


class VectorSearchResponse(BaseModel):
    """Vector search response."""

    results: list[SearchResultItem]


async def _get_node_properties_from_graph(
    node_id: str,
    tenant_id: str,
) -> dict[str, Any]:
    """Fetch full node properties from AGE graph by node id.

    Args:
        node_id: UUID string of the node.
        tenant_id: Clerk org ID for isolation.

    Returns:
        Node properties dict, or minimal fallback if not found.
    """
    try:
        from context_os.graph.client import run_cypher

        pool = get_age_pool()
        rows = await run_cypher(
            pool,
            "MATCH (n {id: $id, tenant_id: $tenant_id}) RETURN n",
            params={"id": node_id, "tenant_id": tenant_id},
            columns=[("n", "agtype")],
        )

        if rows and rows[0].get("n"):
            node_data = rows[0]["n"]
            if isinstance(node_data, dict):
                return node_data.get("properties", node_data)
    except Exception as e:
        logger.debug("Could not fetch node %s from graph: %s", node_id, e)

    return {}


@router.post("/search", response_model=VectorSearchResponse)
async def vector_search(
    request: VectorSearchRequest,
    tenant: TenantContext = Depends(get_current_tenant),
) -> VectorSearchResponse:
    """Semantic top-k similarity search over Memory and Artifact nodes.

    Encodes the query text using all-mpnet-base-v2 and retrieves the k
    nearest neighbors from the node_embeddings table using HNSW cosine index.

    Args:
        request: Search parameters (query, k, node_types).
        tenant: Authenticated tenant context.

    Returns:
        Top-k results with cosine distances and full node properties.

    Raises:
        HTTPException(400): If query is empty.
        HTTPException(500): If vector search fails.
    """
    tracer = _get_tracer()
    trace_id = get_current_trace_id()
    start_time = time.monotonic()

    if not request.query or not request.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "validation_error",
                "message": "query must be a non-empty string",
                "trace_id": trace_id,
            },
        )

    span_ctx = tracer.start_as_current_span("vector.search") if tracer else None

    try:
        if span_ctx:
            span = span_ctx.__enter__()  # type: ignore[attr-defined]
            span.set_attribute("context_os.agent_identity", "vector-search-v1")  # type: ignore[attr-defined]
            span.set_attribute("context_os.autonomy_level", 2)  # type: ignore[attr-defined]
            span.set_attribute("context_os.tenant_id", tenant.tenant_id)  # type: ignore[attr-defined]
            span.set_attribute(  # type: ignore[attr-defined]
                "context_os.input_summary",
                f"query_len={len(request.query)} k={request.k}",
            )
            span.set_attribute("context_os.governance_markers", "{}")  # type: ignore[attr-defined]
            span.set_attribute("gen_ai.system", "context-os")  # type: ignore[attr-defined]
            span.set_attribute("gen_ai.operation.name", "vector_search")  # type: ignore[attr-defined]

        factory = get_session_factory()
        async with factory() as session:
            results = await search(
                session=session,
                tenant_id=tenant.db_tenant_id,
                query_text=request.query,
                k=request.k,
                node_types=request.node_types,
            )

        # Enrich results with full node properties from graph
        result_items = []
        for sr in results:
            node_props = await _get_node_properties_from_graph(
                node_id=sr.node_id,
                tenant_id=tenant.tenant_id,
            )

            provenance = ProvenanceResponse(
                source=str(node_props.get("source", "internal")),
                source_id=str(node_props.get("source_id", "")),
                fetch_ts=str(node_props.get("fetch_ts", "")),
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
            properties = {k: v for k, v in node_props.items() if k not in base_fields}
            # Include content from the embedding record if not in graph props
            if "content" not in properties:
                properties["content"] = sr.content

            node_resp = GraphNodeResponse(
                id=sr.node_id,
                type=sr.node_type,
                tenant_id=tenant.tenant_id,
                provenance=provenance,
                properties=properties,
            )

            result_items.append(SearchResultItem(node=node_resp, distance=sr.distance))

        top_distance = results[0].distance if results else 0.0

        if span_ctx and tracer:
            try:
                span.set_attribute(  # type: ignore[attr-defined]
                    "context_os.output_summary",
                    f"results_returned={len(results)} top_distance={top_distance:.4f}",
                )
            except Exception:
                pass

        duration_ms = (time.monotonic() - start_time) * 1000
        emit_structured_log(
            StructuredLogRecord(
                event=EVENT.VECTOR_SEARCH_EXECUTED,
                message=f"Vector search executed: '{request.query[:50]}'",
                agent_identity="vector-search-v1",
                autonomy_level=2,
                tenant_id=tenant.tenant_id,
                duration_ms=duration_ms,
                trace_id=trace_id,
                metadata={
                    "query_length": len(request.query),
                    "k": request.k,
                    "node_types": request.node_types,
                    "top_distance": top_distance,
                    "results_returned": len(results),
                },
            )
        )

        return VectorSearchResponse(results=result_items)

    except (VectorSearchError, TenantIsolationError) as e:
        duration_ms = (time.monotonic() - start_time) * 1000
        emit_structured_log(
            StructuredLogRecord(
                event=EVENT.VECTOR_SEARCH_ERROR,
                message=f"Vector search failed: {e.message}",
                agent_identity="vector-search-v1",
                autonomy_level=2,
                tenant_id=tenant.tenant_id,
                duration_ms=duration_ms,
                level="ERROR",
                trace_id=trace_id,
                metadata={"error": str(e), "query": request.query[:100]},
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
                "code": "vector_search_error",
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
