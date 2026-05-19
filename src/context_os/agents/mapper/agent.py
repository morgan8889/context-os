"""Dependency Mapper agent: LangGraph StateGraph for dependency discovery.

The Mapper is an autonomy-level-2 agent that:
1. Walks the knowledge graph to collect cross-initiative signal evidence
2. Calls Claude via tool-use loop to classify dependency candidates
3. Enqueues candidates above the confidence threshold as proposed_dependency
   ApprovalItems for operator review

NEVER writes DEPENDS_ON edges to the canonical graph directly — all outputs
go through the ApprovalItem approval gate (constitution Principle III).
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from typing import Any, TypedDict

import anthropic
import asyncpg
from langgraph.graph import END, StateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from context_os.agents.base import AbstractAgent
from context_os.agents.mapper.prompts import (
    MAPPER_CONFIDENCE_THRESHOLD,
    MAPPER_SYSTEM_PROMPT,
    build_mapper_user_prompt,
)
from context_os.agents.mapper.tools import MAPPER_TOOLS, execute_tool
from context_os.config import get_settings
from context_os.core.errors import BudgetExceededError
from context_os.graph.queries import find_cross_initiative_signals_for_mapper
from context_os.relational.repositories import ApprovalItemRepository

logger = logging.getLogger(__name__)


class MapperState(TypedDict, total=False):
    """LangGraph state for the dependency mapping workflow.

    All fields are optional (total=False) because LangGraph merges partial
    state updates at each node — not all fields are populated at every step.
    """

    tenant_id: str
    max_depth: int
    focus_node_id: str | None  # Optional: start walk from specific node
    walk_results: list[dict[str, Any]]  # Raw cross-initiative signals
    candidates: list[dict[str, Any]]  # Classified dependency candidates
    enqueued_count: int  # Number of ApprovalItems created
    cost_tokens: int
    error: str | None


class DependencyMapperAgent(AbstractAgent):
    """Dependency Mapper agent: discovers hidden cross-initiative dependencies.

    Autonomy level 2 — proposed dependencies require operator approval before
    canonical graph promotion. Uses LangGraph StateGraph with optional
    AsyncPostgresSaver for durable checkpoint storage.
    """

    agent_identity = "mapper"
    autonomy_level = 2

    def __init__(
        self,
        tenant_id: str,
        age_pool: asyncpg.Pool,  # type: ignore[type-arg]
        session: AsyncSession,
        checkpointer: Any = None,
    ) -> None:
        """Initialize the Dependency Mapper agent.

        Args:
            tenant_id: Clerk org ID (for graph queries and AGE).
            age_pool: AGE asyncpg pool for graph queries.
            session: SQLAlchemy async session for relational operations.
            checkpointer: Optional LangGraph AsyncPostgresSaver for durability.
        """
        super().__init__(tenant_id)
        self._age_pool = age_pool
        self._session = session
        self._checkpointer = checkpointer
        self._graph = self._build_graph()

    def _build_graph(self) -> Any:
        """Build and compile the LangGraph StateGraph.

        Returns:
            Compiled LangGraph with optional checkpointer.
        """
        workflow = StateGraph(MapperState)

        workflow.add_node("walk_graph", self._walk_graph_node)
        workflow.add_node("classify_candidates", self._classify_candidates_node)
        workflow.add_node("enqueue_proposals", self._enqueue_proposals_node)

        workflow.set_entry_point("walk_graph")
        workflow.add_edge("walk_graph", "classify_candidates")
        workflow.add_edge("classify_candidates", "enqueue_proposals")
        workflow.add_edge("enqueue_proposals", END)

        return workflow.compile(checkpointer=self._checkpointer)

    async def run(self, **kwargs: Any) -> MapperState:
        """Run the dependency mapping workflow.

        Args:
            max_depth: Maximum graph traversal depth (default 3).
            focus_node_id: Optional node ID to start traversal from.
            thread_id: Optional LangGraph thread ID for resumability.

        Returns:
            Final MapperState after all nodes complete.
        """
        max_depth = int(kwargs.get("max_depth", 3))
        focus_node_id = kwargs.get("focus_node_id")
        thread_id = kwargs.get("thread_id", str(uuid.uuid4()))

        initial_state: MapperState = {
            "tenant_id": self._tenant_id,
            "max_depth": max_depth,
            "focus_node_id": focus_node_id,
            "walk_results": [],
            "candidates": [],
            "enqueued_count": 0,
            "cost_tokens": 0,
            "error": None,
        }

        config = {"configurable": {"thread_id": thread_id}}

        start_time = time.monotonic()
        final_state = await self._graph.ainvoke(initial_state, config=config)
        elapsed_ms = int((time.monotonic() - start_time) * 1000)

        cost_tokens = final_state.get("cost_tokens", 0)
        enqueued = final_state.get("enqueued_count", 0)
        signals_count = len(final_state.get("walk_results", []))

        await self._emit_agent_span(
            input_summary=f"max_depth={max_depth} signals={signals_count}",
            output_summary=(
                f"candidates={len(final_state.get('candidates', []))} "
                f"enqueued={enqueued} elapsed_ms={elapsed_ms}"
            ),
            cost_tokens=cost_tokens,
            governance_markers=["requires_approval"],
        )

        return final_state  # type: ignore[return-value]

    # ── LangGraph node implementations ────────────────────────────────────────

    async def _walk_graph_node(self, state: MapperState) -> dict[str, Any]:
        """Walk the graph to find cross-initiative signals.

        Uses find_cross_initiative_signals_for_mapper to gather evidence of
        potential dependency relationships.

        Args:
            state: Current workflow state.

        Returns:
            Partial state update with walk_results.
        """
        tenant_id = state.get("tenant_id", "")
        max_depth = state.get("max_depth", 3)

        try:
            signals = await find_cross_initiative_signals_for_mapper(
                pool=self._age_pool,
                tenant_id=tenant_id,
                max_depth=max_depth,
            )
        except Exception as e:
            logger.warning("walk_graph_node failed for tenant=%s: %s", tenant_id, e)
            signals = []

        logger.info(
            "walk_graph_node: tenant=%s cross_initiative_signals=%d",
            tenant_id,
            len(signals),
        )
        return {"walk_results": signals}

    async def _classify_candidates_node(self, state: MapperState) -> dict[str, Any]:
        """Run the Anthropic tool-use loop to classify dependency candidates.

        Args:
            state: Current workflow state.

        Returns:
            Partial state update with candidates and cost_tokens.
        """
        settings = get_settings()
        tenant_id = state.get("tenant_id", "")
        walk_results = state.get("walk_results", [])

        api_key = settings.anthropic_api_key.get_secret_value()
        if not api_key:
            logger.warning("No ANTHROPIC_API_KEY — returning empty candidates")
            return {
                "candidates": [],
                "cost_tokens": 0,
                "error": "ANTHROPIC_API_KEY not configured",
            }

        client = anthropic.AsyncAnthropic(api_key=api_key)

        # For the prompt, estimate initiative count from walk_results
        initiative_ids: set[str] = set()
        for signal in walk_results:
            # Signals may carry initiative_ids if the query populated them
            for iid in signal.get("initiative_ids", []):
                initiative_ids.add(str(iid))

        user_prompt = build_mapper_user_prompt(
            initiative_count=max(len(initiative_ids), 2 if walk_results else 0),
            signal_count=len(walk_results),
        )

        messages: list[dict[str, Any]] = [{"role": "user", "content": user_prompt}]
        cost_tokens = 0
        budget = settings.briefing_cost_budget_tokens
        raw_output = ""

        try:
            while True:
                response = await client.messages.create(
                    model=settings.anthropic_model,
                    max_tokens=settings.anthropic_max_tokens,
                    system=MAPPER_SYSTEM_PROMPT,
                    tools=MAPPER_TOOLS,  # type: ignore[arg-type]
                    messages=messages,  # type: ignore[arg-type]
                )

                cost_tokens += (
                    response.usage.input_tokens + response.usage.output_tokens
                )

                if cost_tokens > budget:
                    raise BudgetExceededError(
                        tokens_used=cost_tokens,
                        budget=budget,
                        message=(
                            f"Mapper token budget exceeded: {cost_tokens} > {budget}"
                        ),
                    )

                if response.stop_reason == "end_turn":
                    for block in response.content:
                        if isinstance(block, anthropic.types.TextBlock):
                            raw_output = block.text
                            break
                    break

                # Process tool_use blocks
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        try:
                            result = await execute_tool(
                                tool_name=block.name,
                                tool_input=block.input,  # type: ignore[arg-type]
                                tenant_id=tenant_id,
                                age_pool=self._age_pool,
                            )
                        except Exception as exc:
                            result = {"error": str(exc)}

                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": json.dumps(result),
                            }
                        )

                messages.append(
                    {"role": "assistant", "content": response.content}  # type: ignore[arg-type]
                )
                messages.append({"role": "user", "content": tool_results})

        except BudgetExceededError:
            raise
        except Exception as exc:
            logger.error(
                "classify_candidates_node failed: tenant=%s error=%s",
                tenant_id,
                exc,
            )
            return {
                "candidates": [],
                "cost_tokens": cost_tokens,
                "error": str(exc),
            }

        candidates = _parse_candidates_json(raw_output)
        logger.info(
            "classify_candidates_node: tenant=%s raw_candidates=%d cost_tokens=%d",
            tenant_id,
            len(candidates),
            cost_tokens,
        )
        return {
            "candidates": candidates,
            "cost_tokens": cost_tokens,
        }

    async def _enqueue_proposals_node(self, state: MapperState) -> dict[str, Any]:
        """Write qualifying candidates as proposed_dependency ApprovalItems.

        Skips candidates below MAPPER_CONFIDENCE_THRESHOLD and any that would
        duplicate an existing pending or approved proposed_dependency for the
        same (from, to) initiative pair.

        Args:
            state: Current workflow state.

        Returns:
            Partial state update with enqueued_count.
        """
        tenant_id = state.get("tenant_id", "")
        candidates = state.get("candidates", [])

        repo = ApprovalItemRepository(self._session)
        enqueued = 0

        # Fetch existing pending/approved proposed_dependency items to deduplicate
        existing = await repo.list_by_tenant(
            tenant_id=tenant_id,
            item_type="proposed_dependency",
            status="pending",
            limit=1000,
        )
        existing_pairs: set[tuple[str, str]] = set()
        for item in existing:
            content = item.content or {}
            from_id = content.get("from_initiative_id", "")
            to_id = content.get("to_initiative_id", "")
            if from_id and to_id:
                existing_pairs.add((from_id, to_id))

        for candidate in candidates:
            confidence = float(candidate.get("confidence", 0.0))
            if confidence < MAPPER_CONFIDENCE_THRESHOLD:
                logger.debug(
                    "Skipping low-confidence candidate: %.2f < %.2f",
                    confidence,
                    MAPPER_CONFIDENCE_THRESHOLD,
                )
                continue

            from_id = candidate.get("from_initiative_id", "")
            to_id = candidate.get("to_initiative_id", "")

            if not from_id or not to_id:
                logger.warning(
                    "Skipping candidate with missing initiative IDs: %s", candidate
                )
                continue

            # Deduplicate
            pair = (from_id, to_id)
            if pair in existing_pairs:
                logger.debug(
                    "Skipping duplicate proposed_dependency: %s → %s", from_id, to_id
                )
                continue

            content: dict[str, Any] = {
                "from_initiative_id": from_id,
                "to_initiative_id": to_id,
                "confidence": confidence,
                "evidence": candidate.get("evidence_signal_ids", []),
                "dependency_type": candidate.get("dependency_type", "unknown"),
                "description": candidate.get("description", ""),
            }

            try:
                await repo.create(
                    tenant_id=tenant_id,
                    item_type="proposed_dependency",
                    content=content,
                )
                enqueued += 1
                existing_pairs.add(pair)  # Prevent intra-batch duplicates
            except Exception as exc:
                logger.error(
                    "Failed to enqueue proposed_dependency: %s → %s error=%s",
                    from_id,
                    to_id,
                    exc,
                )

        try:
            await self._session.commit()
        except Exception as exc:
            logger.error(
                "enqueue_proposals_node commit failed: tenant=%s error=%s",
                tenant_id,
                exc,
            )

        logger.info(
            "enqueue_proposals_node: tenant=%s enqueued=%d of %d candidates",
            tenant_id,
            enqueued,
            len(candidates),
        )
        return {"enqueued_count": enqueued}


def _parse_candidates_json(raw: str) -> list[dict[str, Any]]:
    """Parse the LLM's raw JSON candidate array.

    Handles common LLM formatting issues like code fences.

    Args:
        raw: Raw string from the LLM response.

    Returns:
        List of candidate dicts, or empty list if parsing fails.
    """
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1]) if len(lines) > 2 else text

    try:
        result = json.loads(text)
        if isinstance(result, list):
            return result
        # If the model wrapped the array in an object
        if isinstance(result, dict):
            for key in ("candidates", "dependencies", "results"):
                if isinstance(result.get(key), list):
                    return result[key]  # type: ignore[return-value]
        return []
    except (json.JSONDecodeError, ValueError) as exc:
        logger.warning("Failed to parse candidates JSON: %s", exc)
        return []
