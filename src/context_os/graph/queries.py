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

# Re-export for type hints used by the synthesizer
__all__ = [
    "TraversalResult",
    "traverse",
    "find_signals_in_window",
    "check_actor_exists",
    "find_stale_dependencies",
    "find_cross_initiative_signals_for_mapper",
    "find_pr_review_patterns",
]

logger = logging.getLogger(__name__)

# ── Phase 2: Synthesizer graph read queries ───────────────────────────────────


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


async def find_signals_in_window(
    pool: asyncpg.Pool,  # type: ignore[type-arg]
    tenant_id: str,
    window_start: str,
    window_end: str,
    sources: list[str] | None = None,
    graph_name: str = "context_os",
) -> list[dict[str, Any]]:
    """Find Signal nodes created within a time window for briefing retrieval.

    Returns Signal nodes with provenance metadata. Used by the Synthesizer agent
    to populate its context before generating a briefing draft.

    Args:
        pool: AGE-configured asyncpg pool.
        tenant_id: Clerk org ID — MUST be non-empty.
        window_start: ISO 8601 start timestamp (inclusive).
        window_end: ISO 8601 end timestamp (inclusive).
        sources: Optional list of source systems to filter on (github, jira, slack).
        graph_name: AGE graph name.

    Returns:
        List of Signal node property dicts.

    Raises:
        TenantIsolationError: If tenant_id is empty.
        GraphQueryError: If the AGE query fails.
    """
    _assert_tenant_id(tenant_id)

    params: dict[str, Any] = {
        "tenant_id": tenant_id,
        "window_start": window_start,
        "window_end": window_end,
    }

    # Build optional source filter
    source_where = ""
    if sources:
        for i, src in enumerate(sources):
            params[f"src_{i}"] = src
        src_conditions = " OR ".join(
            f"n.source = $src_{i}" for i in range(len(sources))
        )
        source_where = f" AND ({src_conditions})"

    cypher = f"""
    MATCH (n:Signal)
    WHERE n.tenant_id = $tenant_id
      AND n.created_at >= $window_start
      AND n.created_at <= $window_end
      {source_where}
    RETURN n
    LIMIT 500
    """

    try:
        rows = await run_cypher(
            pool,
            cypher,
            params=params,
            graph_name=graph_name,
            columns=[("n", "agtype")],
        )
    except Exception as e:
        logger.error(
            "find_signals_in_window failed: tenant=%s window=%s..%s error=%s",
            tenant_id,
            window_start,
            window_end,
            e,
        )
        raise GraphQueryError(
            code="graph_query_error",
            message=f"Signal window query failed: {e}",
        ) from e

    signals = []
    for row in rows:
        node_data = row.get("n")
        if isinstance(node_data, dict):
            props = node_data.get("properties", node_data)
            signals.append(props)
    return signals


async def check_actor_exists(
    pool: asyncpg.Pool,  # type: ignore[type-arg]
    tenant_id: str,
    name_fragment: str,
    graph_name: str = "context_os",
) -> bool:
    """Check whether an Actor node exists with a name matching the given fragment.

    Used by the Synthesizer failure detection to catch hallucinated stakeholder
    names. Returns True if at least one Actor node matches.

    Args:
        pool: AGE-configured asyncpg pool.
        tenant_id: Clerk org ID — MUST be non-empty.
        name_fragment: Name substring to search for (case-insensitive prefix match).
        graph_name: AGE graph name.

    Returns:
        True if a matching Actor exists, False otherwise.

    Raises:
        TenantIsolationError: If tenant_id is empty.
        GraphQueryError: If the AGE query fails.
    """
    _assert_tenant_id(tenant_id)

    params: dict[str, Any] = {
        "tenant_id": tenant_id,
        "name_frag": name_fragment.lower(),
    }

    # AGE does not support CONTAINS directly; use starts-with approximation via
    # toLower. For exact matching the caller should pass the full name.
    cypher = """
    MATCH (a:Actor)
    WHERE a.tenant_id = $tenant_id
      AND toLower(a.name) CONTAINS $name_frag
    RETURN count(a) AS cnt
    LIMIT 1
    """

    try:
        rows = await run_cypher(
            pool,
            cypher,
            params=params,
            graph_name=graph_name,
            columns=[("cnt", "agtype")],
        )
    except Exception as e:
        logger.error(
            "check_actor_exists failed: tenant=%s name=%s error=%s",
            tenant_id,
            name_fragment,
            e,
        )
        raise GraphQueryError(
            code="graph_query_error",
            message=f"Actor existence check failed: {e}",
        ) from e

    if rows:
        count = rows[0].get("cnt", 0)
        return int(count) > 0
    return False


async def find_stale_dependencies(
    pool: asyncpg.Pool,  # type: ignore[type-arg]
    tenant_id: str,
    older_than_days: int = 90,
    graph_name: str = "context_os",
) -> list[dict[str, Any]]:
    """Find DEPENDS_ON edges whose updated_at is older than the threshold.

    Used by the Synthesizer failure detection to flag stale dependencies in
    a briefing draft. A dependency is considered stale if it has not been
    updated in the last `older_than_days` days.

    Args:
        pool: AGE-configured asyncpg pool.
        tenant_id: Clerk org ID — MUST be non-empty.
        older_than_days: Number of days before which an edge is considered stale.
        graph_name: AGE graph name.

    Returns:
        List of DEPENDS_ON edge property dicts that are stale.

    Raises:
        TenantIsolationError: If tenant_id is empty.
        GraphQueryError: If the AGE query fails.
    """
    _assert_tenant_id(tenant_id)

    from datetime import UTC, datetime, timedelta

    threshold = (datetime.now(UTC) - timedelta(days=older_than_days)).isoformat() + "Z"
    params: dict[str, Any] = {
        "tenant_id": tenant_id,
        "threshold": threshold,
    }

    cypher = """
    MATCH (a)-[r:DEPENDS_ON]->(b)
    WHERE r.tenant_id = $tenant_id
      AND r.updated_at < $threshold
    RETURN r
    LIMIT 200
    """

    try:
        rows = await run_cypher(
            pool,
            cypher,
            params=params,
            graph_name=graph_name,
            columns=[("r", "agtype")],
        )
    except Exception as e:
        logger.error(
            "find_stale_dependencies failed: tenant=%s older_than=%d error=%s",
            tenant_id,
            older_than_days,
            e,
        )
        raise GraphQueryError(
            code="graph_query_error",
            message=f"Stale dependency query failed: {e}",
        ) from e

    edges = []
    for row in rows:
        edge_data = row.get("r")
        if isinstance(edge_data, dict):
            props = edge_data.get("properties", edge_data)
            edges.append(props)
    return edges


# ── Phase 2: Dependency Mapper graph queries ──────────────────────────────────


async def find_cross_initiative_signals_for_mapper(
    pool: asyncpg.Pool,  # type: ignore[type-arg]
    tenant_id: str,
    max_depth: int = 3,
    graph_name: str = "context_os",
) -> list[dict[str, Any]]:
    """Find Signals connecting multiple Initiative nodes (walking up to max_depth hops).

    Returns Signal nodes that appear in the vicinity of more than one
    Initiative node, which are potential dependency evidence.

    Args:
        pool: AGE-configured asyncpg pool.
        tenant_id: Clerk org ID — MUST be non-empty.
        max_depth: Maximum traversal depth from Initiative nodes (1–5).
        graph_name: AGE graph name.

    Returns:
        List of Signal node property dicts that appear near multiple Initiatives.

    Raises:
        TenantIsolationError: If tenant_id is empty.
        GraphQueryError: If the AGE query fails.
    """
    _assert_tenant_id(tenant_id)

    if max_depth < 1 or max_depth > 5:
        raise ValueError(f"max_depth must be 1–5, got {max_depth}")

    params: dict[str, Any] = {"tenant_id": tenant_id}

    cypher = f"""
    MATCH (i:Initiative)
    WHERE i.tenant_id = $tenant_id
    MATCH (i)-[*1..{max_depth}]-(s:Signal)
    WHERE s.tenant_id = $tenant_id
    WITH s, collect(DISTINCT i.id) AS initiative_ids
    WHERE size(initiative_ids) > 1
    RETURN s
    LIMIT 100
    """

    try:
        rows = await run_cypher(
            pool,
            cypher,
            params=params,
            graph_name=graph_name,
            columns=[("s", "agtype")],
        )
    except Exception as e:
        logger.error(
            "find_cross_initiative_signals_for_mapper failed: tenant=%s error=%s",
            tenant_id,
            e,
        )
        raise GraphQueryError(
            code="graph_query_error",
            message=f"Cross-initiative signal query failed: {e}",
        ) from e

    signals = []
    for row in rows:
        node_data = row.get("s")
        if isinstance(node_data, dict):
            props = node_data.get("properties", node_data)
            signals.append(props)
    return signals


async def find_pr_review_patterns(
    pool: asyncpg.Pool,  # type: ignore[type-arg]
    tenant_id: str,
    graph_name: str = "context_os",
) -> list[dict[str, Any]]:
    """Find Initiative pairs linked by shared Actor nodes reviewing Artifacts for both.

    Shared reviewers across initiative boundaries indicate implicit cross-team
    dependencies that may warrant explicit DEPENDS_ON edges.

    Args:
        pool: AGE-configured asyncpg pool.
        tenant_id: Clerk org ID — MUST be non-empty.
        graph_name: AGE graph name.

    Returns:
        Dicts with from_initiative_id, to_initiative_id, shared_actor_id, actor_name.

    Raises:
        TenantIsolationError: If tenant_id is empty.
        GraphQueryError: If the AGE query fails.
    """
    _assert_tenant_id(tenant_id)

    params: dict[str, Any] = {"tenant_id": tenant_id}

    # Find Actors who appear as reviewers (via REVIEWED or MENTIONED edges)
    # on Artifacts belonging to more than one Initiative
    cypher = """
    MATCH (actor:Actor)-[:REVIEWED|MENTIONED]->(artifact:Artifact)
    WHERE actor.tenant_id = $tenant_id
      AND artifact.tenant_id = $tenant_id
    MATCH (initiative:Initiative)-[:PRODUCES|IMPLEMENTS]->(artifact)
    WHERE initiative.tenant_id = $tenant_id
    WITH actor, collect(DISTINCT initiative.id) AS initiative_ids
    WHERE size(initiative_ids) > 1
    RETURN actor, initiative_ids
    LIMIT 50
    """

    try:
        rows = await run_cypher(
            pool,
            cypher,
            params=params,
            graph_name=graph_name,
            columns=[("actor", "agtype"), ("initiative_ids", "agtype")],
        )
    except Exception as e:
        logger.error(
            "find_pr_review_patterns failed: tenant=%s error=%s",
            tenant_id,
            e,
        )
        raise GraphQueryError(
            code="graph_query_error",
            message=f"PR review pattern query failed: {e}",
        ) from e

    patterns = []
    for row in rows:
        actor_data = row.get("actor")
        initiative_ids = row.get("initiative_ids", [])
        if isinstance(actor_data, dict):
            actor_props = actor_data.get("properties", actor_data)
            if isinstance(initiative_ids, list) and len(initiative_ids) >= 2:
                for i in range(len(initiative_ids)):
                    for j in range(i + 1, len(initiative_ids)):
                        patterns.append(
                            {
                                "from_initiative_id": initiative_ids[i],
                                "to_initiative_id": initiative_ids[j],
                                "shared_actor_id": actor_props.get("id", ""),
                                "actor_name": actor_props.get("name", ""),
                            }
                        )
    return patterns
