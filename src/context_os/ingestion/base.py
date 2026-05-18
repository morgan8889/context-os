"""Abstract IngestAdapter base class for all integration adapters.

Provides checkpoint management, rate limit handling, and the run() lifecycle.
Concrete adapters implement _fetch_page() and _normalize().

Key invariant: checkpoints are ONLY saved after successful DB commits.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from context_os.core.errors import RateLimitError, TokenExpiredError
from context_os.db.engine import get_session_factory
from context_os.relational.repositories import CheckpointRepository

logger = logging.getLogger(__name__)


@dataclass
class IngestResult:
    """Summary of a completed ingest run.

    Attributes:
        integration: Name of the integration (github, jira, slack).
        records_fetched: Total records retrieved from the API.
        nodes_created: New graph nodes created.
        nodes_updated: Existing graph nodes updated.
        edges_created: New graph edges created.
        checkpoint_cursor: Final cursor value saved to sync_checkpoints.
        error: Error message if the run failed, or None on success.
    """

    integration: str
    records_fetched: int = 0
    nodes_created: int = 0
    nodes_updated: int = 0
    edges_created: int = 0
    checkpoint_cursor: str | None = None
    error: str | None = None


class IngestAdapter(ABC):
    """Abstract base for all integration ingest adapters.

    Subclasses implement _fetch_page() and _normalize() for each source.
    The run() method orchestrates the full ingest lifecycle:
    1. Load checkpoint
    2. Fetch pages (paginated)
    3. Normalize records to BaseNodeSchema
    4. Persist to graph (caller's responsibility via run())
    5. Save checkpoint after successful commit
    """

    def __init__(
        self,
        integration: str,
        tenant_id: str,
        db_tenant_id: uuid.UUID,
        full_sync: bool = False,
    ) -> None:
        """Initialize the adapter.

        Args:
            integration: Integration name (github, jira, slack).
            tenant_id: Clerk org ID string.
            db_tenant_id: Internal tenant UUID for DB operations.
            full_sync: If True, ignore checkpoint and re-ingest all data.
        """
        self.integration = integration
        self.tenant_id = tenant_id
        self.db_tenant_id = db_tenant_id
        self.full_sync = full_sync
        self._checkpoints: dict[str, str | None] = {}

    @abstractmethod
    async def _fetch_page(
        self,
        object_type: str,
        cursor: str | None,
    ) -> tuple[list[dict[str, Any]], str | None]:
        """Fetch one page of raw records from the upstream API.

        Args:
            object_type: The type of object to fetch (issues, prs, messages, etc.).
            cursor: Pagination/incremental sync cursor, or None for first page.

        Returns:
            Tuple of (records, next_cursor). next_cursor is None if last page.

        Raises:
            TokenExpiredError: If the OAuth token is expired or revoked.
            RateLimitError: If the API returns 429.
        """
        ...

    @abstractmethod
    def _normalize(
        self,
        raw_record: dict[str, Any],
        object_type: str,
    ) -> list[dict[str, Any]]:
        """Normalize a raw API record to one or more node property dicts.

        Each returned dict must have 'node_type' and all BaseNodeSchema fields.

        Args:
            raw_record: Raw record from the upstream API.
            object_type: The object type of the record.

        Returns:
            List of normalized node property dicts (may be empty for skipped records).
        """
        ...

    async def _load_checkpoint(self, object_type: str) -> str | None:
        """Load the last sync cursor for this adapter/object_type.

        Args:
            object_type: Object type to retrieve cursor for.

        Returns:
            Cursor value string or None if no checkpoint exists.
        """
        if self.full_sync:
            return None

        if object_type in self._checkpoints:
            return self._checkpoints[object_type]

        factory = get_session_factory()
        async with factory() as session:
            repo = CheckpointRepository(session)
            checkpoint = await repo.get(
                tenant_id=self.db_tenant_id,
                integration=self.integration,
                object_type=object_type,
            )
            cursor = checkpoint.cursor_value if checkpoint else None
            self._checkpoints[object_type] = cursor
            return cursor

    async def _save_checkpoint(
        self,
        object_type: str,
        cursor: str | None,
    ) -> None:
        """Save the sync cursor AFTER a successful DB commit.

        This MUST only be called after all graph and relational writes have
        been committed. Calling this before commit would cause data loss
        if the commit subsequently fails.

        Args:
            object_type: Object type to save cursor for.
            cursor: New cursor value to save.
        """
        factory = get_session_factory()
        async with factory() as session:
            repo = CheckpointRepository(session)
            await repo.upsert(
                tenant_id=self.db_tenant_id,
                integration=self.integration,
                object_type=object_type,
                cursor_value=cursor,
            )
            await session.commit()

        self._checkpoints[object_type] = cursor
        logger.info(
            "Checkpoint saved: integration=%s object_type=%s cursor=%s",
            self.integration,
            object_type,
            cursor,
        )

    async def _handle_rate_limit(self, retry_after: int) -> None:
        """Exponential backoff respecting the Retry-After header value.

        Waits for the specified number of seconds (at minimum) before returning.

        Args:
            retry_after: Seconds to wait per the Retry-After header.
        """
        wait_secs = max(retry_after, 1)
        logger.warning(
            "Rate limited by %s; backing off %ds", self.integration, wait_secs
        )
        await asyncio.sleep(wait_secs)

    def _handle_token_expired(self) -> None:
        """Handle expired OAuth token: raise TokenExpiredError.

        The checkpoint is NOT updated here — it was saved at the last successful
        commit, so ingest can resume from where it left off after token refresh.

        Raises:
            TokenExpiredError: Always.
        """
        raise TokenExpiredError(
            code="token_expired",
            message=f"OAuth token for {self.integration} has expired; "
            "re-run 'cli auth {self.integration}' to refresh, "
            "then re-run ingest to resume from checkpoint",
        )

    async def run(self) -> IngestResult:
        """Execute the full ingest lifecycle for this adapter.

        This base implementation calls fetch_all() which subclasses can
        override. The concrete run() that persists to graph is in api/ingest.py.

        Returns:
            IngestResult summary of the run.
        """
        raise NotImplementedError(
            "IngestAdapter.run() must be implemented by the ingest endpoint, "
            "not the adapter itself. Use fetch_all() to get normalized nodes."
        )

    async def fetch_all(
        self,
        object_types: list[str] | None = None,
    ) -> tuple[list[dict[str, Any]], str | None]:
        """Fetch and normalize all records across all pages.

        Handles pagination, rate limiting, and token expiry. Calls _fetch_page()
        and _normalize() for each page and record.

        Args:
            object_types: List of object types to fetch. Subclasses should
                          define their supported types.

        Returns:
            Tuple of (normalized_nodes, final_cursor).
            normalized_nodes: All nodes ready for graph persistence.
            final_cursor: Last cursor value seen (for checkpoint saving).
        """
        all_nodes: list[dict[str, Any]] = []
        final_cursor: str | None = None

        for obj_type in object_types or self._get_object_types():
            cursor = await self._load_checkpoint(obj_type)
            page_count = 0

            while True:
                try:
                    records, next_cursor = await self._fetch_page(obj_type, cursor)
                except RateLimitError as e:
                    await self._handle_rate_limit(e.retry_after)
                    # Retry same page
                    continue
                except TokenExpiredError:
                    self._handle_token_expired()
                    break  # unreachable, but satisfies type checker

                for record in records:
                    try:
                        nodes = self._normalize(record, obj_type)
                        all_nodes.extend(nodes)
                    except Exception as e:
                        logger.warning("Failed to normalize %s record: %s", obj_type, e)

                page_count += 1
                if next_cursor:
                    cursor = next_cursor
                    final_cursor = next_cursor
                else:
                    final_cursor = cursor
                    break

            logger.info(
                "Fetched %s: object_type=%s pages=%d records=%d",
                self.integration,
                obj_type,
                page_count,
                len(all_nodes),
            )

        return all_nodes, final_cursor

    def _get_object_types(self) -> list[str]:
        """Return the list of object types this adapter supports.

        Override in subclasses to specify supported types.
        """
        return []
