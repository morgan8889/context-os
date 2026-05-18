"""BriefingWorkflow: orchestrates the end-to-end briefing generation lifecycle.

Responsible for:
1. Creating the BriefingRun record (status=generating)
2. Instantiating and running the SynthesizerAgent LangGraph
3. Updating BriefingRun on completion or failure
4. Resuming suspended LangGraph threads after operator approval actions
"""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

import asyncpg
from sqlalchemy.ext.asyncio import AsyncSession

from context_os.agents.synthesizer.agent import SynthesizerAgent
from context_os.core.errors import WorkflowError
from context_os.relational.repositories import (
    BriefingRunRepository,
)

logger = logging.getLogger(__name__)


@dataclass
class BriefingRunStatus:
    """Status of a briefing generation run.

    Attributes:
        run_id: UUID string of the BriefingRun record.
        status: generating | complete | failed | partial.
        tenant_id: Clerk org ID.
        approval_item_id: UUID of the enqueued ApprovalItem (when complete).
        cost_tokens: Total token cost for this run.
        latency_ms: Total generation time in milliseconds.
        error: Error detail if status=failed.
        window_start: ISO 8601 start of the briefing window.
        window_end: ISO 8601 end of the briefing window.
    """

    run_id: str
    status: str
    tenant_id: str
    approval_item_id: str | None = None
    cost_tokens: int | None = None
    latency_ms: int | None = None
    error: str | None = None
    window_start: str | None = None
    window_end: str | None = None


class BriefingWorkflow:
    """Orchestrates the full briefing generation lifecycle.

    Encapsulates BriefingRun state management, SynthesizerAgent invocation,
    and LangGraph thread resume for post-approval actions.
    """

    # Minimum signal count to proceed with generation (< this → low_signal flag)
    MIN_SIGNAL_COUNT = 5

    # Stale data threshold: if last ingest > this many days ago, set data_stale
    STALE_INGEST_DAYS = 7

    def __init__(
        self,
        age_pool: asyncpg.Pool,  # type: ignore[type-arg]
        session: AsyncSession,
        checkpointer: Any,
    ) -> None:
        """Initialize the BriefingWorkflow.

        Args:
            age_pool: AGE asyncpg pool for graph queries.
            session: SQLAlchemy async session for relational operations.
            checkpointer: LangGraph AsyncPostgresSaver for durable checkpoints.
        """
        self._age_pool = age_pool
        self._session = session
        self._checkpointer = checkpointer

    async def start(
        self,
        tenant_id: str,
        db_tenant_id: str,
        window_days: int = 7,
        trigger_type: str = "manual",
    ) -> BriefingRunStatus:
        """Create a new briefing run and invoke the Synthesizer agent.

        Creates a BriefingRun record, runs the SynthesizerAgent, and updates
        the BriefingRun to complete/failed when the agent finishes.

        Args:
            tenant_id: Clerk org ID (for AGE graph queries).
            db_tenant_id: Internal DB UUID string (for relational queries).
            window_days: Number of days in the briefing window (default 7).
            trigger_type: manual | scheduled.

        Returns:
            BriefingRunStatus with run_id and final status.

        Raises:
            WorkflowError: If the BriefingRun cannot be created.
        """
        now = datetime.now(UTC)
        window_end = now
        window_start = now - timedelta(days=window_days)

        # 1. Create BriefingRun record
        run_repo = BriefingRunRepository(self._session)
        try:
            run = await run_repo.create(
                tenant_id=tenant_id,
                trigger_type=trigger_type,
                window_days=window_days,
                window_start=window_start,
                window_end=window_end,
            )
            await self._session.commit()
            run_id = str(run.id)
        except Exception as e:
            raise WorkflowError(
                message=f"Failed to create BriefingRun: {e}",
                thread_id=None,
            ) from e

        thread_id = str(uuid.uuid4())
        start_time = time.monotonic()

        # 2. Instantiate and run the SynthesizerAgent
        agent = SynthesizerAgent(
            tenant_id=tenant_id,
            db_tenant_id=db_tenant_id,
            age_pool=self._age_pool,
            session=self._session,
            checkpointer=self._checkpointer,
        )

        try:
            final_state = await agent.run(
                window_days=window_days,
                run_id=run_id,
                thread_id=thread_id,
            )

            elapsed_ms = int((time.monotonic() - start_time) * 1000)
            cost_tokens = final_state.get("cost_tokens", 0)
            approval_item_id = final_state.get("approval_item_id")
            error = final_state.get("error")
            signals = final_state.get("signals_retrieved", [])

            # Compute signal counts by source
            signal_counts: dict[str, int] = {}
            for signal in signals:
                src = signal.get("source", "unknown")
                signal_counts[src] = signal_counts.get(src, 0) + 1

            final_status = "complete" if not error else "failed"

            # 3. Update BriefingRun with results
            await run_repo.update_status(
                run_id=run.id,
                tenant_id=tenant_id,
                status=final_status,
                cost_tokens=cost_tokens,
                latency_ms=elapsed_ms,
                error_detail=error,
                approval_item_id=(
                    uuid.UUID(approval_item_id) if approval_item_id else None
                ),
                input_signal_counts=signal_counts,
            )
            await self._session.commit()

            logger.info(
                "BriefingWorkflow.start complete: run_id=%s status=%s "
                "cost_tokens=%d latency_ms=%d",
                run_id,
                final_status,
                cost_tokens,
                elapsed_ms,
            )

            return BriefingRunStatus(
                run_id=run_id,
                status=final_status,
                tenant_id=tenant_id,
                approval_item_id=approval_item_id,
                cost_tokens=cost_tokens,
                latency_ms=elapsed_ms,
                error=error,
                window_start=window_start.isoformat() + "Z",
                window_end=window_end.isoformat() + "Z",
            )

        except Exception as e:
            elapsed_ms = int((time.monotonic() - start_time) * 1000)
            error_detail = str(e)
            logger.error(
                "BriefingWorkflow.start failed: run_id=%s error=%s",
                run_id,
                error_detail,
            )

            # Update run to failed
            try:
                await run_repo.update_status(
                    run_id=run.id,
                    tenant_id=tenant_id,
                    status="failed",
                    latency_ms=elapsed_ms,
                    error_detail=error_detail,
                )
                await self._session.commit()
            except Exception as commit_err:
                logger.warning("Failed to update BriefingRun to failed: %s", commit_err)

            raise WorkflowError(
                message=f"Briefing workflow failed: {e}",
                thread_id=thread_id,
            ) from e

    async def resume(
        self,
        thread_id: str,
        operator_action: str,
        edited_content: dict[str, Any] | None = None,
    ) -> None:
        """Resume a suspended LangGraph workflow thread after operator action.

        Called after an operator approves or rejects an ApprovalItem that has
        a workflow_thread_id. Resumes the LangGraph with the operator's decision
        injected into state.

        Args:
            thread_id: LangGraph thread ID to resume.
            operator_action: 'approve' | 'reject'.
            edited_content: Optional edited content for edit-then-approve flows.
        """
        try:
            # For simple approval flows (no interrupt_before configured),
            # the graph has already completed -- this is a no-op for Phase 2.
            # In Phase 3+ the graph would be resumed via graph.ainvoke with
            # the operator state injected using:
            #   config = {"configurable": {"thread_id": thread_id}}
            #   resume_state = {"operator_action": operator_action,
            #                   "edited_content": edited_content}
            logger.info(
                "BriefingWorkflow.resume: thread_id=%s action=%s",
                thread_id,
                operator_action,
            )
        except Exception as e:
            logger.warning(
                "BriefingWorkflow.resume failed: thread_id=%s error=%s",
                thread_id,
                e,
            )
            raise WorkflowError(
                message=f"Failed to resume workflow thread {thread_id}: {e}",
                thread_id=thread_id,
            ) from e


async def get_workflow(
    age_pool: asyncpg.Pool,  # type: ignore[type-arg]
    session: AsyncSession,
    checkpointer: Any,
) -> BriefingWorkflow:
    """Factory: create a BriefingWorkflow instance.

    Args:
        age_pool: AGE asyncpg pool.
        session: SQLAlchemy async session.
        checkpointer: LangGraph AsyncPostgresSaver.

    Returns:
        Configured BriefingWorkflow instance.
    """
    return BriefingWorkflow(
        age_pool=age_pool,
        session=session,
        checkpointer=checkpointer,
    )
