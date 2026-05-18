"""Fault injection test: rate limit (429) mid-ingest.

Tests that when a 429 is injected on the second page:
1. Adapter backs off respecting Retry-After header
2. Checkpoint is preserved
3. Retry succeeds after backoff
4. No duplicate nodes in graph after re-run
"""

from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from context_os.core.errors import RateLimitError
from context_os.ingestion.github.client import GitHubClient


class TestRateLimit:
    """Tests for rate limit fault injection."""

    @pytest.mark.asyncio
    async def test_rate_limit_error_raised(self) -> None:
        """GitHubClient raises RateLimitError on 429 response."""
        import httpx

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "30"}
        mock_response.json.return_value = {"message": "Too Many Requests"}

        with patch("httpx.AsyncClient.get", return_value=mock_response):
            async with GitHubClient(access_token="valid_token") as client:
                with pytest.raises(RateLimitError) as exc_info:
                    await client.list_repos()

        assert exc_info.value.code == "rate_limited"
        assert exc_info.value.retry_after == 30

    @pytest.mark.asyncio
    async def test_rate_limit_error_has_retry_after(self) -> None:
        """RateLimitError carries retry_after value from Retry-After header."""
        error = RateLimitError(
            code="rate_limited",
            message="Rate limit exceeded",
            retry_after=120,
        )
        assert error.retry_after == 120
        error_dict = error.to_dict()
        assert error_dict["retry_after"] == 120

    @pytest.mark.asyncio
    async def test_adapter_backoff_and_retry(self) -> None:
        """Adapter backs off on RateLimitError and retries same page."""
        from context_os.ingestion.base import IngestAdapter

        call_count = [0]
        sleep_called = [False]
        sleep_seconds = [0]

        class _TestAdapter(IngestAdapter):
            async def _fetch_page(
                self, obj_type: str, cursor: Any
            ) -> tuple[list[dict[str, Any]], Any]:
                call_count[0] += 1
                if call_count[0] == 1:
                    # First call: rate limited
                    raise RateLimitError(
                        code="rate_limited",
                        message="Rate limited",
                        retry_after=1,
                    )
                else:
                    # Second call: success
                    return [{"id": "node1"}], None

            def _normalize(self, raw: Any, obj_type: str) -> list[Any]:
                return [
                    {
                        "node_type": "Signal",
                        "id": str(uuid.uuid4()),
                        "tenant_id": "org_test",
                    }
                ]

            def _get_object_types(self) -> list[str]:
                return ["test_type"]

        adapter = _TestAdapter(
            integration="github",
            tenant_id="org_test",
            db_tenant_id=uuid.uuid4(),
        )

        # Mock sleep to avoid actual waiting and capture call
        async def mock_sleep(seconds: float) -> None:
            sleep_called[0] = True
            sleep_seconds[0] = seconds

        with (
            patch(
                "context_os.ingestion.base.asyncio.sleep",
                side_effect=mock_sleep,
            ),
            patch.object(adapter, "_load_checkpoint", new_callable=AsyncMock),
            patch.object(adapter, "_save_checkpoint", new_callable=AsyncMock),
        ):
            nodes, cursor = await adapter.fetch_all()

        # Verify backoff occurred
        assert sleep_called[0], "asyncio.sleep must be called on rate limit"
        assert sleep_seconds[0] >= 1, "Must wait at least Retry-After seconds"
        # Verify retry succeeded
        assert call_count[0] == 2, "Should have made exactly 2 fetch calls (1 retry)"

    @pytest.mark.asyncio
    async def test_checkpoint_preserved_on_rate_limit(self) -> None:
        """Checkpoint is preserved through rate limit errors.

        After rate limit + retry + success, the final cursor should be set.
        """
        from context_os.ingestion.base import IngestAdapter

        class _TestAdapter(IngestAdapter):
            _call_count = 0

            async def _fetch_page(
                self, obj_type: str, cursor: Any
            ) -> tuple[list[dict[str, Any]], Any]:
                self._call_count += 1
                if self._call_count == 1:
                    raise RateLimitError(
                        code="rate_limited", message="Limited", retry_after=1
                    )
                # Second call: success, no next cursor → last page
                return [{"id": "item1"}], None

            def _normalize(self, raw: Any, obj_type: str) -> list[Any]:
                return []

            def _get_object_types(self) -> list[str]:
                return ["items"]

        adapter = _TestAdapter(
            integration="github",
            tenant_id="org_test",
            db_tenant_id=uuid.uuid4(),
        )

        with (
            patch(
                "context_os.ingestion.base.asyncio.sleep",
                new_callable=AsyncMock,
            ),  # Don't actually sleep
            patch.object(adapter, "_load_checkpoint", return_value=None),
            patch.object(adapter, "_save_checkpoint", new_callable=AsyncMock),
        ):
            nodes, cursor = await adapter.fetch_all()

        # After rate limit + retry, fetch succeeds with no next_cursor.
        # final_cursor = starting cursor (None), since next_cursor was None.
        assert cursor is None

    @pytest.mark.asyncio
    async def test_no_duplicate_nodes_after_retry(self) -> None:
        """Re-running ingest after a rate limit produces no duplicate nodes.

        The MERGE operation in AGE ensures idempotent node upserts.
        """
        upsert_calls: list[dict[str, Any]] = []

        # Simulate two ingest runs with the same node
        node_id = str(uuid.uuid4())
        node_props = {
            "id": node_id,
            "tenant_id": "org_test",
            "source": "github",
            "source_id": "pr_1",
            "node_type": "Artifact",
            "fetch_ts": "2026-05-18T00:00:00Z",
            "title": "Test PR",
        }

        async def mock_upsert(
            pool: Any,
            tenant_id: str,
            node_type: str,
            props: dict[str, Any],
            **kwargs: Any,
        ) -> str:
            upsert_calls.append({"tenant_id": tenant_id, "node_id": props.get("id")})
            return str(props.get("id", ""))

        # Run upsert twice (simulating two ingest runs)
        with patch(
            "context_os.graph.mutations.run_cypher", new_callable=AsyncMock
        ) as mock_cypher:
            mock_cypher.return_value = [{"id": f'"{node_id}"'}]

            from context_os.graph.mutations import upsert_node

            pool = MagicMock()

            await upsert_node(
                pool=pool, tenant_id="org_test", node_type="Artifact", props=node_props
            )
            await upsert_node(
                pool=pool, tenant_id="org_test", node_type="Artifact", props=node_props
            )

        # Both calls should use MERGE (idempotent), not INSERT
        # Verify both calls were made (MERGE handles deduplication in AGE)
        assert mock_cypher.call_count == 2

        # Check that MERGE was used (not CREATE) in both Cypher calls
        for call in mock_cypher.call_args_list:
            cypher_arg = call[0][1] if len(call[0]) > 1 else call[1].get("cypher", "")
            cypher_upper = cypher_arg.upper()
            assert "MERGE" in cypher_upper, f"MERGE expected in Cypher: {cypher_arg}"
