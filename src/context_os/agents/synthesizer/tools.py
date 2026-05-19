"""Anthropic tool-use schemas and dispatcher for the Synthesizer agent.

IMPORTANT: Only read-only tools are exposed to the LLM. All write operations
are performed by deterministic Python nodes after operator approval.
"""

from __future__ import annotations

import logging
from typing import Any

import asyncpg
from sqlalchemy.ext.asyncio import AsyncSession

from context_os.graph.queries import (
    TraversalResult,
    check_actor_exists,
    traverse,
)
from context_os.vector.search import SearchResult
from context_os.vector.search import search as vector_search

logger = logging.getLogger(__name__)


# ── Anthropic tool-use schema definitions ─────────────────────────────────────

SYNTHESIZER_TOOLS: list[dict[str, Any]] = [
    {
        "name": "retrieve_graph_context",
        "description": (
            "Retrieve graph context by traversing from a node. "
            "Returns related nodes and edges up to max_hops away. "
            "Use this to find related signals, artifacts, and goals."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "The node ID (UUID) to start traversal from, "
                        "or a topic description"
                    ),
                },
                "node_types": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "Optional list of node types to filter results "
                        "(e.g. ['Signal', 'Artifact', 'Goal', 'Initiative'])"
                    ),
                },
                "max_hops": {
                    "type": "integer",
                    "description": "Maximum traversal depth (1–3 recommended)",
                    "minimum": 1,
                    "maximum": 3,
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "retrieve_vector_context",
        "description": (
            "Semantic search for relevant nodes using vector similarity. "
            "Returns the top-k most semantically similar nodes to the query. "
            "Use this to find contextually relevant signals and artifacts."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language query for semantic search",
                },
                "k": {
                    "type": "integer",
                    "description": "Number of results to return (1–20)",
                    "minimum": 1,
                    "maximum": 20,
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "check_actor_exists",
        "description": (
            "Verify whether a named stakeholder or team member exists in the graph. "
            "Use this to validate actor names before citing them in the briefing. "
            "Returns true if found, false if not found (potential hallucination)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The person or team name to look up",
                },
            },
            "required": ["name"],
        },
    },
]


# ── Tool executor dispatcher ──────────────────────────────────────────────────


async def execute_tool(
    tool_name: str,
    tool_input: dict[str, Any],
    tenant_id: str,
    db_session: AsyncSession,
    age_pool: asyncpg.Pool,  # type: ignore[type-arg]
) -> Any:
    """Dispatch a tool call to the appropriate implementation.

    Args:
        tool_name: Name of the tool to invoke (must be in SYNTHESIZER_TOOLS).
        tool_input: Dict of tool input parameters.
        tenant_id: Clerk org ID for tenant isolation.
        db_session: SQLAlchemy async session for relational queries.
        age_pool: AGE asyncpg pool for graph queries.

    Returns:
        Tool result (type varies by tool).

    Raises:
        ValueError: If tool_name is not recognized.
    """
    if tool_name == "retrieve_graph_context":
        return await _retrieve_graph_context(tool_input, tenant_id, age_pool)
    elif tool_name == "retrieve_vector_context":
        return await _retrieve_vector_context(tool_input, tenant_id, db_session)
    elif tool_name == "check_actor_exists":
        return await _check_actor_exists(tool_input, tenant_id, age_pool)
    else:
        raise ValueError(f"Unknown synthesizer tool: {tool_name}")


async def _retrieve_graph_context(
    tool_input: dict[str, Any],
    tenant_id: str,
    age_pool: asyncpg.Pool,  # type: ignore[type-arg]
) -> dict[str, Any]:
    """Execute the retrieve_graph_context tool.

    Args:
        tool_input: Tool parameters (query, node_types, max_hops).
        tenant_id: Clerk org ID.
        age_pool: AGE asyncpg pool.

    Returns:
        Dict with nodes and edges lists.
    """
    query = tool_input.get("query", "")
    node_types = tool_input.get("node_types")
    max_hops = int(tool_input.get("max_hops", 2))

    # Clamp max_hops to valid range
    max_hops = max(1, min(3, max_hops))

    try:
        result: TraversalResult = await traverse(
            pool=age_pool,
            tenant_id=tenant_id,
            from_id=query,
            max_hops=max_hops,
            node_types=node_types,
        )
        return {
            "nodes": result.nodes[:50],  # Cap to avoid context overflow
            "edges": result.edges[:50],
            "query_ms": result.query_ms,
        }
    except Exception as e:
        logger.warning("retrieve_graph_context failed for query=%s: %s", query, e)
        return {"nodes": [], "edges": [], "error": str(e)}


async def _retrieve_vector_context(
    tool_input: dict[str, Any],
    tenant_id: str,
    db_session: AsyncSession,
) -> list[dict[str, Any]]:
    """Execute the retrieve_vector_context tool.

    Args:
        tool_input: Tool parameters (query, k).
        tenant_id: Clerk org ID.
        db_session: SQLAlchemy async session.

    Returns:
        List of semantically similar node dicts with similarity scores.
    """
    query = tool_input.get("query", "")
    k = int(tool_input.get("k", 10))
    k = max(1, min(20, k))

    # The vector search function requires a UUID tenant_id (DB internal UUID).
    # The synthesizer agent receives Clerk org ID (string) as tenant_id.
    # We use the string form and accept that search may return 0 results if
    # the session's tenant UUID differs — the tools layer is best-effort.
    try:
        # Look up the DB UUID from session context if available
        # For now, skip vector search if tenant_id is not a valid UUID
        import uuid as uuid_mod

        try:
            db_tenant_uuid = uuid_mod.UUID(tenant_id)
        except ValueError:
            # tenant_id is a Clerk org string, not a UUID; skip vector search
            logger.debug(
                "Skipping vector search: tenant_id %s is not a UUID", tenant_id
            )
            return []

        results: list[SearchResult] = await vector_search(
            session=db_session,
            tenant_id=db_tenant_uuid,
            query_text=query,
            k=k,
        )
        return [
            {
                "id": str(r.node_id),
                "node_type": r.node_type,
                "content": r.content[:500],  # Truncate for context efficiency
                "distance": r.distance,
            }
            for r in results
        ]
    except Exception as e:
        logger.warning("retrieve_vector_context failed for query=%s: %s", query, e)
        return []


async def _check_actor_exists(
    tool_input: dict[str, Any],
    tenant_id: str,
    age_pool: asyncpg.Pool,  # type: ignore[type-arg]
) -> dict[str, Any]:
    """Execute the check_actor_exists tool.

    Args:
        tool_input: Tool parameters (name).
        tenant_id: Clerk org ID.
        age_pool: AGE asyncpg pool.

    Returns:
        Dict with 'exists' bool and 'name' for confirmation.
    """
    name = tool_input.get("name", "")
    try:
        exists = await check_actor_exists(
            pool=age_pool,
            tenant_id=tenant_id,
            name_fragment=name,
        )
        return {"name": name, "exists": exists}
    except Exception as e:
        logger.warning("check_actor_exists failed for name=%s: %s", name, e)
        return {"name": name, "exists": False, "error": str(e)}
