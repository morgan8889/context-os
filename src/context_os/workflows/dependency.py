"""DependencyWorkflow: orchestrates the dependency mapper scan lifecycle.

Responsible for:
1. Preventing concurrent scans per tenant (in-memory conflict check)
2. Instantiating and running the DependencyMapperAgent LangGraph
3. Returning a MapperScanStatus with the count of proposed dependencies
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import asyncpg
from sqlalchemy.ext.asyncio import AsyncSession

from context_os.agents.mapper.agent import DependencyMapperAgent

logger = logging.getLogger(__name__)

# In-memory set of tenant_ids with an active scan.
# Scans are stateless (no BriefingRun equivalent) — only a 409 conflict check
# is needed, not durable run tracking.
_active_scans: set[str] = set()


@dataclass
class MapperScanStatus:
    """Status returned after a dependency mapper scan.

    Attributes:
        tenant_id: Clerk org ID of the scanning tenant.
        proposed_count: Number of proposed_dependency ApprovalItems enqueued.
        status: completed | failed.
        error: Error detail if status=failed.
    """

    tenant_id: str
    proposed_count: int
    status: str
    error: str | None = None


class DependencyWorkflow:
    """Orchestrates the dependency mapper scan lifecycle.

    Tracks active scans in-memory to prevent concurrent scans per tenant.
    Scans are stateless — status is computed from approval items rather than
    a dedicated run record.
    """

    def __init__(
        self,
        age_pool: asyncpg.Pool,  # type: ignore[type-arg]
        session: AsyncSession,
        checkpointer: Any = None,
    ) -> None:
        """Initialize the DependencyWorkflow.

        Args:
            age_pool: AGE asyncpg pool for graph queries.
            session: SQLAlchemy async session for relational operations.
            checkpointer: Optional LangGraph AsyncPostgresSaver for durability.
        """
        self._age_pool = age_pool
        self._session = session
        self._checkpointer = checkpointer

    @staticmethod
    def is_active(tenant_id: str) -> bool:
        """Return True if a scan is currently active for this tenant.

        Args:
            tenant_id: Clerk org ID to check.

        Returns:
            True if an active scan exists.
        """
        return tenant_id in _active_scans

    async def scan(
        self,
        tenant_id: str,
        max_depth: int = 3,
        focus_node_id: str | None = None,
    ) -> MapperScanStatus:
        """Run a dependency mapper scan for the given tenant.

        Instantiates DependencyMapperAgent, runs the LangGraph, and returns
        a MapperScanStatus with the number of proposed_dependency items enqueued.

        Registers the tenant in the active scans set for the duration of the scan
        to prevent concurrent invocations.

        Args:
            tenant_id: Clerk org ID (for graph queries and relational operations).
            max_depth: Maximum graph traversal depth (default 3).
            focus_node_id: Optional node ID to start traversal from.

        Returns:
            MapperScanStatus with proposed_count and status.
        """
        if tenant_id in _active_scans:
            logger.warning(
                "DependencyWorkflow.scan: concurrent scan rejected for tenant=%s",
                tenant_id,
            )
            return MapperScanStatus(
                tenant_id=tenant_id,
                proposed_count=0,
                status="failed",
                error="A scan is already active for this tenant.",
            )

        _active_scans.add(tenant_id)
        logger.info(
            "DependencyWorkflow.scan starting: tenant=%s max_depth=%d",
            tenant_id,
            max_depth,
        )

        try:
            agent = DependencyMapperAgent(
                tenant_id=tenant_id,
                age_pool=self._age_pool,
                session=self._session,
                checkpointer=self._checkpointer,
            )

            final_state = await agent.run(
                max_depth=max_depth,
                focus_node_id=focus_node_id,
            )

            proposed_count = final_state.get("enqueued_count", 0)
            error = final_state.get("error")
            scan_status = "completed" if not error else "failed"

            logger.info(
                "DependencyWorkflow.scan complete: tenant=%s proposed=%d status=%s",
                tenant_id,
                proposed_count,
                scan_status,
            )

            return MapperScanStatus(
                tenant_id=tenant_id,
                proposed_count=proposed_count,
                status=scan_status,
                error=error,
            )

        except Exception as exc:
            logger.error(
                "DependencyWorkflow.scan failed: tenant=%s error=%s",
                tenant_id,
                exc,
            )
            return MapperScanStatus(
                tenant_id=tenant_id,
                proposed_count=0,
                status="failed",
                error=str(exc),
            )

        finally:
            _active_scans.discard(tenant_id)
