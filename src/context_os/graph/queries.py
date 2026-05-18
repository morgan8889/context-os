"""Graph traversal queries using Apache AGE Cypher.

All queries enforce tenant_id isolation. User values are passed via
AGE parameter map — never interpolated into Cypher strings.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

import asyncpg

from context_os.core.errors import GraphQueryError, TenantIsolationError
from context_os.graph.client import run_cypher

logger = logging.getLogger(__name__)


def _assert_tenant_id(tenant_id: str | None) -> None:
    """Raise TenantIsolationError if tenant_id is empty or None.

    Args:
        tenant_id: Tenant identifier to validate.

    Raises:
        TenantIsolationError: If tenant_id is falsy or empty.
    """
    if not tenant_id:
        raise TenantIsolationError(
            code="tenant_isolation_error",
            message="tenant_id is required for all graph queries",
        )


@dataclass
class TraversalResult:
    """Result of a graph traversal query.

    Attributes:
        nodes: List of node property dicts returned by the traversal.
        edges: List of edge property dicts returned by the traversal.
        query_ms: Total query execution time in milliseconds.
    """

    nodes: list[dict[str, Any]] = field(default_factory=list)
    edges: list[dict[str, Any]] = field(default_factory=list)
    query_ms: float = 0.0


async def traverse(
    pool: asyncpg.Pool,  # type: ignore[type-arg]
    tenant_id: str,
    from_id: str,
    max_hops: int = 1,
    edge_types: list[str] | None = None,
    node_types: list[str] | None = None,
    graph_name: str = "context_os",
) -> TraversalResult:
    """Traverse the graph from a starting node.

    Performs 1-hop to k-hop traversal using Cypher variable-length path syntax.
    Results are filtered by tenant_id to enforce isolation.

    Args:
        pool: AGE-configured asyncpg pool.
        tenant_id: Clerk org ID — MUST be non-empty.
        from_id: UUID string of the starting node.
        max_hops: Maximum traversal depth (1–5).
        edge_types: Optional list of edge labels to filter on.
        node_types: Optional list of node type property values to filter on.
        graph_name: AGE graph name.

    Returns:
        TraversalResult with nodes, edges, and query timing.

    Raises:
        TenantIsolationError: If tenant_id is empty.
        GraphQueryError: If the AGE query fails.
        ValueError: If max_hops is out of range.
    """
    _assert_tenant_id(tenant_id)

    if max_hops < 1 or max_hops > 5:
        raise ValueError(f"max_hops must be between 1 and 5, got {max_hops}")

    params: dict[str, Any] = {
        "from_id": from_id,
        "tenant_id": tenant_id,
    }

    # Build edge type filter clause
    if edge_types:
        # AGE supports [r:TYPE1|TYPE2] syntax for multiple edge types
        edge_label = "|".join(edge_types)
        edge_pattern = f"[r:{edge_label}*1..{max_hops}]"
    else:
        edge_pattern = f"[r*1..{max_hops}]"

    # Build node type WHERE filter
    node_where_parts = ["end.tenant_id = $tenant_id"]
    if node_types:
        # node_type is stored as a property, not an AGE label
        params["node_types"] = node_types
        # AGE doesn't support IN for agtype arrays directly, use OR
        type_conditions = " OR ".join(
            f"end.node_type = $node_type_{i}" for i in range(len(node_types))
        )
        for i, nt in enumerate(node_types):
            params[f"node_type_{i}"] = nt
        node_where_parts.append(f"({type_conditions})")

    where_clause = " AND ".join(node_where_parts)

    # The Cypher traversal query
    cypher = f"""
    MATCH (start {{id: $from_id, tenant_id: $tenant_id}})
    MATCH (start)-{edge_pattern}->(end)
    WHERE {where_clause}
    RETURN start, r, end
    """

    start_time = time.monotonic()

    try:
        rows = await run_cypher(
            pool,
            cypher,
            params=params,
            graph_name=graph_name,
            columns=[
                ("start_node", "agtype"),
                ("rel", "agtype"),
                ("end_node", "agtype"),
            ],
        )
    except Exception as e:
        query_ms = (time.monotonic() - start_time) * 1000
        logger.error(
            "Graph traversal failed: from=%s hops=%d tenant=%s error=%s",
            from_id,
            max_hops,
            tenant_id,
            e,
        )
        raise GraphQueryError(
            code="graph_query_error",
            message=f"Graph traversal failed: {e}",
        ) from e

    query_ms = (time.monotonic() - start_time) * 1000

    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    seen_node_ids: set[str] = set()
    seen_edge_ids: set[str] = set()

    for row in rows:
        # Extract start node (may already be seen from a previous row)
        start_data = row.get("start_node")
        if isinstance(start_data, dict):
            props = start_data.get("properties", start_data)
            node_id = str(props.get("id", ""))
            if node_id and node_id not in seen_node_ids:
                nodes.append(props)
                seen_node_ids.add(node_id)

        # Extract relationship
        rel_data = row.get("rel")
        if isinstance(rel_data, dict):
            edge_id = str(rel_data.get("id", rel_data.get("start_id", "")))
            if edge_id and edge_id not in seen_edge_ids:
                edges.append(rel_data)
                seen_edge_ids.add(edge_id)

        # Extract end node
        end_data = row.get("end_node")
        if isinstance(end_data, dict):
            props = end_data.get("properties", end_data)
            node_id = str(props.get("id", ""))
            if node_id and node_id not in seen_node_ids:
                nodes.append(props)
                seen_node_ids.add(node_id)

    logger.debug(
        "Graph traversal complete: from=%s hops=%d nodes=%d edges=%d ms=%.1f",
        from_id,
        max_hops,
        len(nodes),
        len(edges),
        query_ms,
    )

    return TraversalResult(nodes=nodes, edges=edges, query_ms=query_ms)
