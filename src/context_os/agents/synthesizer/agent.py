"""Synthesizer agent: LangGraph StateGraph for weekly briefing generation.

The Synthesizer is an autonomy-level-2 agent that:
1. Retrieves signals from the graph and vector stores
2. Calls Claude via tool-use loop to produce a structured briefing draft
3. Runs failure-mode detection on the draft
4. Enqueues the draft as a pending ApprovalItem for operator review

NEVER writes to the canonical AGE graph directly — all outputs go through
the ApprovalItem approval gate (constitution Principle III).
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, TypedDict

import anthropic
import asyncpg
from langgraph.graph import END, StateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from context_os.agents.base import AbstractAgent
from context_os.agents.synthesizer.failure_detection import (
    FailureFlag,
    run_all_failure_checks,
)
from context_os.agents.synthesizer.prompts import (
    BRIEFING_SYSTEM_PROMPT,
    build_briefing_user_prompt,
)
from context_os.agents.synthesizer.tools import SYNTHESIZER_TOOLS, execute_tool
from context_os.config import get_settings
from context_os.core.errors import BudgetExceededError
from context_os.graph.queries import find_signals_in_window
from context_os.relational.repositories import (
    ApprovalItemRepository,
)

logger = logging.getLogger(__name__)


class BriefingState(TypedDict, total=False):
    """LangGraph state for the briefing generation workflow.

    All fields are optional (total=False) because LangGraph merges partial
    state updates at each node — not all fields are populated at every step.
    """

    tenant_id: str
    db_tenant_id: str  # DB UUID string for relational queries
    window_start: str  # ISO 8601
    window_end: str  # ISO 8601
    window_days: int
    signals_retrieved: list[dict[str, Any]]
    draft_sections: dict[str, Any]  # Parsed LLM output
    raw_draft: str  # Raw LLM JSON string for provenance
    failure_flags: list[dict[str, Any]]
    cost_tokens: int
    approval_item_id: str | None
    run_id: str | None
    error: str | None
    low_signal: bool
    data_stale: bool


class SynthesizerAgent(AbstractAgent):
    """Operational Synthesizer agent: produces weekly briefing drafts.

    Autonomy level 2 — outputs require operator approval before canonical
    graph promotion. Uses LangGraph StateGraph with AsyncPostgresSaver for
    durable checkpoint storage.
    """

    agent_identity = "synthesizer"
    autonomy_level = 2

    def __init__(
        self,
        tenant_id: str,
        db_tenant_id: str,
        age_pool: asyncpg.Pool,  # type: ignore[type-arg]
        session: AsyncSession,
        checkpointer: Any,
    ) -> None:
        """Initialize the Synthesizer agent.

        Args:
            tenant_id: Clerk org ID (for graph queries and AGE).
            db_tenant_id: Internal DB UUID string (for relational queries).
            age_pool: AGE asyncpg pool for graph queries.
            session: SQLAlchemy async session for relational operations.
            checkpointer: LangGraph AsyncPostgresSaver for checkpoint persistence.
        """
        super().__init__(tenant_id)
        self._db_tenant_id = db_tenant_id
        self._age_pool = age_pool
        self._session = session
        self._checkpointer = checkpointer
        self._graph = self._build_graph()

    def _build_graph(self) -> Any:
        """Build and compile the LangGraph StateGraph.

        Returns:
            Compiled LangGraph with AsyncPostgresSaver checkpointer.
        """
        workflow = StateGraph(BriefingState)

        workflow.add_node("retrieve_signals", self._retrieve_signals_node)
        workflow.add_node("synthesize_draft", self._synthesize_draft_node)
        workflow.add_node("detect_failures", self._detect_failures_node)
        workflow.add_node("enqueue_approval", self._enqueue_approval_node)

        workflow.set_entry_point("retrieve_signals")
        workflow.add_edge("retrieve_signals", "synthesize_draft")
        workflow.add_edge("synthesize_draft", "detect_failures")
        workflow.add_edge("detect_failures", "enqueue_approval")
        workflow.add_edge("enqueue_approval", END)

        return workflow.compile(checkpointer=self._checkpointer)

    async def run(self, **kwargs: Any) -> BriefingState:
        """Run the briefing generation workflow.

        Args:
            window_days: Number of days for the briefing window (default 7).
            run_id: Optional BriefingRun UUID string.
            thread_id: Optional LangGraph thread ID for resumability.

        Returns:
            Final BriefingState after all nodes complete.
        """
        window_days = int(kwargs.get("window_days", 7))
        run_id = kwargs.get("run_id")
        thread_id = kwargs.get("thread_id", str(uuid.uuid4()))

        now = datetime.now(UTC)
        window_end = now.isoformat() + "Z"
        window_start = (now - timedelta(days=window_days)).isoformat() + "Z"

        initial_state: BriefingState = {
            "tenant_id": self._tenant_id,
            "db_tenant_id": self._db_tenant_id,
            "window_start": window_start,
            "window_end": window_end,
            "window_days": window_days,
            "signals_retrieved": [],
            "draft_sections": {},
            "raw_draft": "",
            "failure_flags": [],
            "cost_tokens": 0,
            "approval_item_id": None,
            "run_id": run_id,
            "error": None,
            "low_signal": False,
            "data_stale": False,
        }

        config = {"configurable": {"thread_id": thread_id}}

        start_time = time.monotonic()
        final_state = await self._graph.ainvoke(initial_state, config=config)
        elapsed_ms = int((time.monotonic() - start_time) * 1000)

        cost_tokens = final_state.get("cost_tokens", 0)
        signals_count = len(final_state.get("signals_retrieved", []))
        flags_count = len(final_state.get("failure_flags", []))

        await self._emit_agent_span(
            input_summary=f"window={window_days}d signals={signals_count}",
            output_summary=(
                f"draft_sections={len(final_state.get('draft_sections', {}))} "
                f"flags={flags_count} elapsed_ms={elapsed_ms}"
            ),
            cost_tokens=cost_tokens,
            governance_markers=["requires_approval"],
        )

        return final_state  # type: ignore[return-value]

    # ── LangGraph node implementations ────────────────────────────────────────

    async def _retrieve_signals_node(self, state: BriefingState) -> dict[str, Any]:
        """Retrieve Signal nodes from the graph within the briefing window.

        Args:
            state: Current workflow state.

        Returns:
            Partial state update with signals_retrieved.
        """
        tenant_id = state.get("tenant_id", "")
        window_start = state.get("window_start", "")
        window_end = state.get("window_end", "")

        try:
            signals = await find_signals_in_window(
                pool=self._age_pool,
                tenant_id=tenant_id,
                window_start=window_start,
                window_end=window_end,
            )
        except Exception as e:
            logger.warning(
                "retrieve_signals_node failed for tenant=%s: %s", tenant_id, e
            )
            signals = []

        low_signal = len(signals) < 5
        logger.info(
            "retrieve_signals_node: tenant=%s signals=%d low_signal=%s",
            tenant_id,
            len(signals),
            low_signal,
        )
        return {
            "signals_retrieved": signals,
            "low_signal": low_signal,
        }

    async def _synthesize_draft_node(self, state: BriefingState) -> dict[str, Any]:
        """Run the Anthropic tool-use loop to produce a briefing draft.

        Args:
            state: Current workflow state.

        Returns:
            Partial state update with draft_sections, raw_draft, cost_tokens.

        Raises:
            BudgetExceededError: If token cost exceeds BRIEFING_COST_BUDGET_TOKENS.
        """
        settings = get_settings()
        tenant_id = state.get("tenant_id", "")
        signals = state.get("signals_retrieved", [])
        window_start = state.get("window_start", "")
        window_end = state.get("window_end", "")
        data_stale = state.get("data_stale", False)

        api_key = settings.anthropic_api_key.get_secret_value()
        if not api_key:
            logger.warning("No ANTHROPIC_API_KEY — returning empty draft")
            return {
                "draft_sections": _empty_draft_sections(),
                "raw_draft": "{}",
                "cost_tokens": 0,
                "error": "ANTHROPIC_API_KEY not configured",
            }

        client = anthropic.AsyncAnthropic(api_key=api_key)

        user_prompt = build_briefing_user_prompt(
            window_start=window_start,
            window_end=window_end,
            signal_count=len(signals),
            data_stale=data_stale,
        )

        messages: list[dict[str, Any]] = [{"role": "user", "content": user_prompt}]
        cost_tokens = 0
        budget = settings.briefing_cost_budget_tokens

        try:
            while True:
                response = await client.messages.create(
                    model=settings.anthropic_model,
                    max_tokens=settings.anthropic_max_tokens,
                    system=BRIEFING_SYSTEM_PROMPT,
                    tools=SYNTHESIZER_TOOLS,  # type: ignore[arg-type]
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
                            f"Briefing token budget exceeded: {cost_tokens} > {budget}"
                        ),
                    )

                if response.stop_reason == "end_turn":
                    # Extract the final text content
                    raw_draft = ""
                    for block in response.content:
                        if isinstance(block, anthropic.types.TextBlock):
                            raw_draft = block.text
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
                                db_session=self._session,
                                age_pool=self._age_pool,
                            )
                        except Exception as e:
                            result = {"error": str(e)}

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
        except Exception as e:
            logger.error(
                "synthesize_draft_node failed: tenant=%s error=%s", tenant_id, e
            )
            return {
                "draft_sections": _empty_draft_sections(),
                "raw_draft": "{}",
                "cost_tokens": cost_tokens,
                "error": str(e),
            }

        # Parse the raw draft JSON
        draft_sections = _parse_draft_json(raw_draft)

        logger.info(
            "synthesize_draft_node complete: tenant=%s cost_tokens=%d",
            tenant_id,
            cost_tokens,
        )
        return {
            "draft_sections": draft_sections,
            "raw_draft": raw_draft,
            "cost_tokens": cost_tokens,
        }

    async def _detect_failures_node(self, state: BriefingState) -> dict[str, Any]:
        """Run all 4 failure-mode checks against the draft.

        Args:
            state: Current workflow state.

        Returns:
            Partial state update with failure_flags list.
        """
        tenant_id = state.get("tenant_id", "")
        draft_sections = state.get("draft_sections", {})

        try:
            flags: list[FailureFlag] = await run_all_failure_checks(
                draft=draft_sections,
                tenant_id=tenant_id,
                age_pool=self._age_pool,
                session=self._session,
            )
            flag_dicts = [f.to_dict() for f in flags]
        except Exception as e:
            logger.warning(
                "detect_failures_node failed: tenant=%s error=%s", tenant_id, e
            )
            flag_dicts = []

        logger.info(
            "detect_failures_node: tenant=%s flags=%d",
            tenant_id,
            len(flag_dicts),
        )
        return {"failure_flags": flag_dicts}

    async def _enqueue_approval_node(self, state: BriefingState) -> dict[str, Any]:
        """Write the draft as a pending ApprovalItem.

        Args:
            state: Current workflow state.

        Returns:
            Partial state update with approval_item_id.
        """
        tenant_id = state.get("tenant_id", "")
        draft_sections = state.get("draft_sections", {})
        failure_flags = state.get("failure_flags", [])
        window_start = state.get("window_start", "")
        window_end = state.get("window_end", "")
        window_days = state.get("window_days", 7)
        low_signal = state.get("low_signal", False)
        data_stale = state.get("data_stale", False)
        run_id_str = state.get("run_id")
        signals = state.get("signals_retrieved", [])

        # Build signal_counts from retrieved signals
        signal_counts: dict[str, int] = {}
        for signal in signals:
            src = signal.get("source", "unknown")
            signal_counts[src] = signal_counts.get(src, 0) + 1

        content: dict[str, Any] = {
            "window_days": window_days,
            "window_start": window_start,
            "window_end": window_end,
            "sections": draft_sections.get("sections", draft_sections),
            "low_signal": low_signal,
            "data_stale": data_stale,
            "signal_counts": signal_counts,
        }

        run_id = uuid.UUID(run_id_str) if run_id_str else None
        failure_flags_dict: dict[str, Any] = {"flags": failure_flags}

        try:
            repo = ApprovalItemRepository(self._session)
            item = await repo.create(
                tenant_id=tenant_id,
                item_type="briefing_draft",
                content=content,
                failure_flags=failure_flags_dict if failure_flags else None,
                run_id=run_id,
            )
            await self._session.commit()
            approval_item_id = str(item.id)

            logger.info(
                "enqueue_approval_node: tenant=%s approval_item_id=%s",
                tenant_id,
                approval_item_id,
            )
            return {"approval_item_id": approval_item_id}

        except Exception as e:
            logger.error(
                "enqueue_approval_node failed: tenant=%s error=%s", tenant_id, e
            )
            return {"approval_item_id": None, "error": str(e)}


def _empty_draft_sections() -> dict[str, Any]:
    """Return an empty but valid briefing draft structure."""
    empty_item = {"text": "No data available for this period.", "source_ids": []}
    return {
        "sections": {
            "progress": [empty_item],
            "risks": [
                {
                    "text": "No risks detected.",
                    "severity": "low",
                    "source_ids": [],
                }
            ],
            "decisions": [empty_item],
            "dependencies": [empty_item],
            "escalations": [empty_item],
        }
    }


def _parse_draft_json(raw: str) -> dict[str, Any]:
    """Parse the LLM's raw JSON output into a briefing draft dict.

    Handles common LLM formatting issues like code fences and extra whitespace.

    Args:
        raw: Raw string from the LLM response.

    Returns:
        Parsed briefing dict, or empty draft structure if parsing fails.
    """
    # Strip markdown code fences if present
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first line (``` or ```json) and last ``` line
        text = "\n".join(lines[1:-1]) if len(lines) > 2 else text

    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning("Failed to parse draft JSON: %s — returning empty draft", e)
        return _empty_draft_sections()
