"""Dependency Mapper agent tools — read-only graph traversal for the LLM.

All tools expose only read operations to the LLM. Write paths (creating
proposed_dependency ApprovalItems) are deterministic Python nodes in the
LangGraph StateGraph, executed after the LLM has classified candidates.

Autonomy level: 2 — read-only retrieval, all writes human-gated.
"""

from __future__ import annotations

import logging
from typing import Any

import asyncpg

from context_os.graph.queries import (
    find_cross_initiative_signals_for_mapper,
    traverse,
)

logger = logging.getLogger(__name__)

# ── Anthropic tool-use schema definitions ─────────────────────────────────────

MAPPER_TOOLS: list[dict[str, Any]] = [
    {
        "name": "walk_graph",
        "description": (
            "Walk the knowledge graph from a starting node up to max_depth "
            "hops. Returns the nodes and edges encountered, filtered by "
            "edge_types if provided. Use this to explore initiative boundaries "
            "and discover connected artifacts, signals, and actors that may "
            "indicate dependency relationships."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "start_node_id": {
                    "type": "string",
                    "description": "UUID string of the node to start traversal from.",
                },
                "max_depth": {
                    "type": "integer",
                    "description": "Maximum number of hops to traverse (1–5).",
                    "minimum": 1,
                    "maximum": 5,
                },
                "edge_types": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "Optional list of edge relationship types to follow "
                        "(e.g. DEPENDS_ON, PRODUCES, IMPLEMENTS, REVIEWED). "
                        "If empty, all edge types are traversed."
                    ),
                },
            },
            "required": ["start_node_id", "max_depth"],
        },
    },
    {
        "name": "find_cross_initiative_signals",
        "description": (
            "Find Signal nodes that appear in the graph neighborhood of more "
            "than one Initiative node, up to max_depth hops from each "
            "Initiative. These cross-initiative signals are strong evidence "
            "of undocumented dependency relationships. Returns a list of "
            "Signal node properties including source, content, and the "
            "initiative IDs they connect."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "max_depth": {
                    "type": "integer",
                    "description": "Maximum hops from each Initiative node (1–5).",
                    "minimum": 1,
                    "maximum": 5,
                },
            },
            "required": ["max_depth"],
        },
    },
]


# ── Tool dispatcher ────────────────────────────────────────────────────────────


async def execute_tool(
    tool_name: str,
    tool_input: dict[str, Any],
    tenant_id: str,
    age_pool: asyncpg.Pool,  # type: ignore[type-arg]
) -> dict[str, Any]:
    """Dispatch a tool call from the Anthropic tool-use loop.

    Routes tool_name to the appropriate graph query function and returns
    the result as a dict suitable for inclusion in the Anthropic messages
    list as a tool_result block.

    Args:
        tool_name: Name of the tool as returned by the Anthropic API.
        tool_input: Tool input parameters from the API response.
        tenant_id: Clerk org ID — enforced in all underlying queries.
        age_pool: AGE asyncpg pool for graph queries.

    Returns:
        Dict with tool results (nodes, edges, or signals).

    Raises:
        ValueError: If tool_name is not recognized.
    """
    if tool_name == "walk_graph":
        return await _walk_graph(
            start_node_id=tool_input["start_node_id"],
            max_depth=int(tool_input["max_depth"]),
            edge_types=tool_input.get("edge_types") or [],
            tenant_id=tenant_id,
            age_pool=age_pool,
        )

    if tool_name == "find_cross_initiative_signals":
        return await _find_cross_initiative_signals(
            max_depth=int(tool_input["max_depth"]),
            tenant_id=tenant_id,
            age_pool=age_pool,
        )

    raise ValueError(f"Unknown mapper tool: {tool_name!r}")


# ── Tool implementations ──────────────────────────────────────────────────────


async def _walk_graph(
    start_node_id: str,
    max_depth: int,
    edge_types: list[str],
    tenant_id: str,
    age_pool: asyncpg.Pool,  # type: ignore[type-arg]
) -> dict[str, Any]:
    """Execute the walk_graph tool.

    Args:
        start_node_id: UUID string of the starting node.
        max_depth: Maximum traversal depth.
        edge_types: Edge relationship type filters.
        tenant_id: Clerk org ID.
        age_pool: AGE asyncpg pool.

    Returns:
        Dict with nodes and edges lists.
    """
    try:
        result = await traverse(
            pool=age_pool,
            tenant_id=tenant_id,
            from_id=start_node_id,
            max_hops=max_depth,
            edge_types=edge_types if edge_types else None,
        )
        return {
            "nodes": result.nodes,
            "edges": result.edges,
            "node_count": len(result.nodes),
            "edge_count": len(result.edges),
            "query_ms": round(result.query_ms, 1),
        }
    except Exception as exc:
        logger.warning(
            "walk_graph tool failed: start=%s depth=%d error=%s",
            start_node_id,
            max_depth,
            exc,
        )
        return {
            "nodes": [],
            "edges": [],
            "node_count": 0,
            "edge_count": 0,
            "error": str(exc),
        }


async def _find_cross_initiative_signals(
    max_depth: int,
    tenant_id: str,
    age_pool: asyncpg.Pool,  # type: ignore[type-arg]
) -> dict[str, Any]:
    """Execute the find_cross_initiative_signals tool.

    Args:
        max_depth: Maximum traversal depth from each Initiative node.
        tenant_id: Clerk org ID.
        age_pool: AGE asyncpg pool.

    Returns:
        Dict with signals list and count.
    """
    try:
        signals = await find_cross_initiative_signals_for_mapper(
            pool=age_pool,
            tenant_id=tenant_id,
            max_depth=max_depth,
        )
        return {
            "signals": signals,
            "signal_count": len(signals),
        }
    except Exception as exc:
        logger.warning(
            "find_cross_initiative_signals tool failed: depth=%d error=%s",
            max_depth,
            exc,
        )
        return {"signals": [], "signal_count": 0, "error": str(exc)}
