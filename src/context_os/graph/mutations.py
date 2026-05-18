"""Graph mutation operations: node and edge upserts with provenance.

All operations enforce tenant_id as a mandatory property. User values are
passed via AGE parameter map — never interpolated into Cypher strings.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

import asyncpg

from context_os.core.errors import TenantIsolationError
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
            message="tenant_id is required for all graph operations",
        )


def _now_iso() -> str:
    """Return current UTC time as ISO 8601 string."""
    return datetime.now(UTC).isoformat() + "Z"


async def upsert_node(
    pool: asyncpg.Pool,  # type: ignore[type-arg]
    tenant_id: str,
    node_type: str,
    props: dict[str, Any],
    graph_name: str = "context_os",
) -> str:
    """Upsert a graph node by (id, tenant_id).

    Uses MERGE to avoid duplicates. ON CREATE SET applies all properties;
    ON MATCH SET updates updated_at and fetch_ts to reflect the latest sync.

    Args:
        pool: AGE-configured asyncpg pool.
        tenant_id: Clerk org ID — MUST be non-empty.
        node_type: AGE label for the node (Goal, Initiative, Signal, etc.).
        props: All node properties including 'id' and 'source_id'.
        graph_name: AGE graph name.

    Returns:
        The node's id string from props.

    Raises:
        TenantIsolationError: If tenant_id is empty.
        KeyError: If 'id' is not in props.
    """
    _assert_tenant_id(tenant_id)

    node_id = str(props["id"])
    now = _now_iso()

    # Build the full params dict for AGE parameter map
    # All values must be JSON-serializable (convert UUID/datetime to str)
    serialized_props: dict[str, Any] = {}
    for k, v in props.items():
        if hasattr(v, "isoformat"):
            serialized_props[k] = v.isoformat() + "Z"
        else:
            serialized_props[k] = str(v) if v is not None else None

    serialized_props["tenant_id"] = tenant_id
    serialized_props["updated_at"] = now
    serialized_props["fetch_ts"] = serialized_props.get("fetch_ts", now)

    # Build ON CREATE SET clause for all props
    create_set_parts = []
    for k in serialized_props:
        create_set_parts.append(f"n.{k} = ${k}")
    create_set_clause = ", ".join(create_set_parts)

    cypher = f"""
    MERGE (n:{node_type} {{id: $id, tenant_id: $tenant_id}})
    ON CREATE SET {create_set_clause}
    ON MATCH SET n.updated_at = $updated_at, n.fetch_ts = $fetch_ts
    RETURN n.id AS id
    """

    params_with_id: dict[str, Any] = {**serialized_props, "id": node_id}

    try:
        await run_cypher(
            pool,
            cypher,
            params=params_with_id,
            graph_name=graph_name,
            columns=[("id", "agtype")],
        )
    except Exception as e:
        logger.error("Failed to upsert node type=%s id=%s: %s", node_type, node_id, e)
        raise

    return node_id


async def upsert_edge(
    pool: asyncpg.Pool,  # type: ignore[type-arg]
    tenant_id: str,
    from_id: str,
    to_id: str,
    edge_type: str,
    props: dict[str, Any] | None = None,
    graph_name: str = "context_os",
) -> None:
    """Upsert a directed edge between two nodes.

    Uses MERGE on the relationship type between nodes matched by (id, tenant_id).

    Args:
        pool: AGE-configured asyncpg pool.
        tenant_id: Clerk org ID — MUST be non-empty.
        from_id: Source node UUID string.
        to_id: Target node UUID string.
        edge_type: AGE edge label (IMPLEMENTS, PRODUCES, etc.).
        props: Optional edge properties.
        graph_name: AGE graph name.

    Raises:
        TenantIsolationError: If tenant_id is empty.
    """
    _assert_tenant_id(tenant_id)

    edge_props: dict[str, Any] = props or {}
    edge_props["tenant_id"] = tenant_id
    edge_props["created_at"] = _now_iso()

    params: dict[str, Any] = {
        "from_id": from_id,
        "to_id": to_id,
        "tenant_id": tenant_id,
        **{f"ep_{k}": str(v) if v is not None else None for k, v in edge_props.items()},
    }

    # Build SET clause for edge properties
    set_parts = [f"r.{k} = $ep_{k}" for k in edge_props]
    set_clause = ", ".join(set_parts) if set_parts else "r.created_at = $ep_created_at"

    cypher = f"""
    MATCH (a {{id: $from_id, tenant_id: $tenant_id}})
    MATCH (b {{id: $to_id, tenant_id: $tenant_id}})
    MERGE (a)-[r:{edge_type}]->(b)
    ON CREATE SET {set_clause}
    RETURN r
    """

    try:
        await run_cypher(
            pool,
            cypher,
            params=params,
            graph_name=graph_name,
            columns=[("r", "agtype")],
        )
    except Exception as e:
        logger.error(
            "Failed to upsert edge %s->%s type=%s: %s", from_id, to_id, edge_type, e
        )
        raise


async def upsert_pending_edge(
    pool: asyncpg.Pool,  # type: ignore[type-arg]
    tenant_id: str,
    from_id: str,
    to_source_id: str,
    to_source: str,
    dependency_type: str,
    graph_name: str = "context_os",
) -> None:
    """Create a DEPENDS_ON edge with resolved=false for cross-source references.

    Used when a Slack message references a GitHub PR that may not yet be
    in the graph. The edge is marked resolved=false and can be resolved
    in a later ingest cycle.

    Args:
        pool: AGE-configured asyncpg pool.
        tenant_id: Clerk org ID — MUST be non-empty.
        from_id: UUID of the source node (e.g. Slack Signal node).
        to_source_id: The vendor source_id of the target node (e.g. PR URL).
        to_source: Source system of the target (e.g. "github").
        dependency_type: Type of dependency (e.g. "references").
        graph_name: AGE graph name.

    Raises:
        TenantIsolationError: If tenant_id is empty.
    """
    _assert_tenant_id(tenant_id)

    params: dict[str, Any] = {
        "from_id": from_id,
        "to_source_id": to_source_id,
        "to_source": to_source,
        "tenant_id": tenant_id,
        "dependency_type": dependency_type,
        "resolved": "false",
        "created_at": _now_iso(),
    }

    cypher = """
    MATCH (a {id: $from_id, tenant_id: $tenant_id})
    MERGE (a)-[r:DEPENDS_ON {to_source_id: $to_source_id, to_source: $to_source}]->(a)
    ON CREATE SET
        r.tenant_id = $tenant_id,
        r.dependency_type = $dependency_type,
        r.resolved = $resolved,
        r.created_at = $created_at
    RETURN r
    """

    try:
        await run_cypher(
            pool,
            cypher,
            params=params,
            graph_name=graph_name,
            columns=[("r", "agtype")],
        )
    except Exception as e:
        logger.warning(
            "Failed to create pending edge from=%s to_source_id=%s: %s",
            from_id,
            to_source_id,
            e,
        )
        # Pending edges are best-effort — don't fail ingest on missing target node


async def get_nodes_for_tenant(
    pool: asyncpg.Pool,  # type: ignore[type-arg]
    tenant_id: str,
    node_type: str | None = None,
    source: str | None = None,
    limit: int = 100,
    offset: int = 0,
    graph_name: str = "context_os",
) -> tuple[list[dict[str, Any]], int]:
    """Retrieve all nodes for a tenant with optional type and source filters.

    Args:
        pool: AGE-configured asyncpg pool.
        tenant_id: Clerk org ID — MUST be non-empty.
        node_type: Optional AGE label filter.
        source: Optional source filter (github, jira, slack, internal).
        limit: Maximum number of nodes to return.
        offset: Pagination offset.
        graph_name: AGE graph name.

    Returns:
        Tuple of (nodes_list, total_count).

    Raises:
        TenantIsolationError: If tenant_id is empty.
    """
    _assert_tenant_id(tenant_id)

    params: dict[str, Any] = {"tenant_id": tenant_id}

    where_parts = ["n.tenant_id = $tenant_id"]

    if node_type:
        params["node_type"] = node_type

    if source:
        params["source"] = source
        where_parts.append("n.source = $source")

    where_clause = " AND ".join(where_parts)
    type_filter = f":{node_type}" if node_type else ""

    # Get total count
    count_cypher = f"""
    MATCH (n{type_filter})
    WHERE {where_clause}
    RETURN count(n) AS cnt
    """

    count_params = {**params}
    count_results = await run_cypher(
        pool,
        count_cypher,
        params=count_params,
        graph_name=graph_name,
        columns=[("cnt", "agtype")],
    )
    total = int(count_results[0]["cnt"]) if count_results else 0

    # Get paginated nodes
    params["limit"] = limit
    params["offset"] = offset

    data_cypher = f"""
    MATCH (n{type_filter})
    WHERE {where_clause}
    RETURN n
    SKIP $offset
    LIMIT $limit
    """

    rows = await run_cypher(
        pool,
        data_cypher,
        params=params,
        graph_name=graph_name,
        columns=[("n", "agtype")],
    )

    nodes = []
    for row in rows:
        node_data = row.get("n")
        if isinstance(node_data, dict):
            # AGE vertex has 'id', 'label', 'properties' structure
            props = node_data.get("properties", node_data)
            nodes.append(props)
        elif node_data is not None:
            nodes.append({"raw": str(node_data)})

    return nodes, total
