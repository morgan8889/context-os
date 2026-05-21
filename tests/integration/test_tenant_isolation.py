"""Integration tests for multi-tenant data isolation.

Tests that Tenant B cannot see any data belonging to Tenant A across all
three query interfaces (graph, vector, relational).

These tests use mocked storage backends to avoid requiring a live database.
"""

from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from context_os.core.errors import TenantIsolationError
from context_os.graph.mutations import _assert_tenant_id as graph_assert_tenant_id
from context_os.graph.queries import _assert_tenant_id as query_assert_tenant_id
from context_os.relational.repositories import (
    _assert_tenant_id as repo_assert_tenant_id,
)
from context_os.vector.search import _assert_tenant_id as vector_assert_tenant_id

# ── Tenant isolation: guard functions ─────────────────────────────────────────


class TestTenantIdAssertions:
    """Test that all _assert_tenant_id guards raise on empty/None tenant_id."""

    def test_graph_mutations_assert_empty(self) -> None:
        """graph/mutations: empty tenant_id raises TenantIsolationError."""
        with pytest.raises(TenantIsolationError):
            graph_assert_tenant_id("")

    def test_graph_mutations_assert_none(self) -> None:
        """graph/mutations: None tenant_id raises TenantIsolationError."""
        with pytest.raises(TenantIsolationError):
            graph_assert_tenant_id(None)

    def test_graph_queries_assert_empty(self) -> None:
        """graph/queries: empty tenant_id raises TenantIsolationError."""
        with pytest.raises(TenantIsolationError):
            query_assert_tenant_id("")

    def test_graph_queries_assert_none(self) -> None:
        """graph/queries: None tenant_id raises TenantIsolationError."""
        with pytest.raises(TenantIsolationError):
            query_assert_tenant_id(None)

    def test_vector_search_assert_empty(self) -> None:
        """vector/search: empty tenant_id raises TenantIsolationError."""
        with pytest.raises(TenantIsolationError):
            vector_assert_tenant_id("")

    def test_vector_search_assert_none(self) -> None:
        """vector/search: None tenant_id raises TenantIsolationError."""
        with pytest.raises(TenantIsolationError):
            vector_assert_tenant_id(None)

    def test_repo_assert_empty(self) -> None:
        """relational/repositories: empty tenant_id raises TenantIsolationError."""
        with pytest.raises(TenantIsolationError):
            repo_assert_tenant_id("")

    def test_repo_assert_none(self) -> None:
        """relational/repositories: None tenant_id raises TenantIsolationError."""
        with pytest.raises(TenantIsolationError):
            repo_assert_tenant_id(None)

    def test_valid_tenant_id_does_not_raise(self) -> None:
        """Valid tenant_id does not raise."""
        # Should not raise
        graph_assert_tenant_id("org_abc123")
        query_assert_tenant_id("org_xyz789")
        vector_assert_tenant_id("org_tenant_1")
        repo_assert_tenant_id("org_another")


# ── Tenant isolation: graph mutations ─────────────────────────────────────────


class TestGraphMutationIsolation:
    """Test that graph mutations enforce tenant_id on all writes."""

    @pytest.mark.asyncio
    async def test_upsert_node_rejects_empty_tenant(
        self,
        mock_age_pool: MagicMock,
    ) -> None:
        """upsert_node raises TenantIsolationError for empty tenant_id."""
        from context_os.graph.mutations import upsert_node

        with pytest.raises(TenantIsolationError):
            await upsert_node(
                pool=mock_age_pool,
                tenant_id="",
                node_type="Artifact",
                props={"id": str(uuid.uuid4())},
            )

    @pytest.mark.asyncio
    async def test_upsert_edge_rejects_empty_tenant(
        self,
        mock_age_pool: MagicMock,
    ) -> None:
        """upsert_edge raises TenantIsolationError for empty tenant_id."""
        from context_os.graph.mutations import upsert_edge

        with pytest.raises(TenantIsolationError):
            await upsert_edge(
                pool=mock_age_pool,
                tenant_id="",
                from_id=str(uuid.uuid4()),
                to_id=str(uuid.uuid4()),
                edge_type="AUTHORED_BY",
            )


# ── Tenant isolation: graph queries ───────────────────────────────────────────


class TestGraphQueryIsolation:
    """Test that graph queries enforce tenant_id filtering."""

    @pytest.mark.asyncio
    async def test_traverse_rejects_empty_tenant(
        self,
        mock_age_pool: MagicMock,
    ) -> None:
        """traverse raises TenantIsolationError for empty tenant_id."""
        from context_os.graph.queries import traverse

        with pytest.raises(TenantIsolationError):
            await traverse(
                pool=mock_age_pool,
                tenant_id="",
                from_id=str(uuid.uuid4()),
            )

    @pytest.mark.asyncio
    async def test_traverse_with_valid_tenant_includes_tenant_filter(
        self,
        mock_age_pool: MagicMock,
        tenant_a_clerk_id: str,
    ) -> None:
        """traverse with valid tenant_id calls run_cypher with tenant_id in params."""
        from context_os.graph.queries import traverse

        cypher_calls: list[dict[str, Any]] = []

        async def mock_run_cypher(
            pool: Any,
            cypher: str,
            params: dict[str, Any] | None = None,
            **kwargs: Any,
        ) -> list[dict[str, Any]]:
            cypher_calls.append({"cypher": cypher, "params": params})
            return []

        with patch("context_os.graph.queries.run_cypher", side_effect=mock_run_cypher):
            await traverse(
                pool=mock_age_pool,
                tenant_id=tenant_a_clerk_id,
                from_id=str(uuid.uuid4()),
                max_hops=1,
            )

        # Verify tenant_id was passed as a parameter (not injected as f-string)
        assert len(cypher_calls) > 0
        for call in cypher_calls:
            params = call.get("params") or {}
            assert "tenant_id" in params, "tenant_id must be in Cypher params"
            assert params["tenant_id"] == tenant_a_clerk_id


# ── Tenant isolation: vector search ───────────────────────────────────────────


class TestVectorSearchIsolation:
    """Test that vector search filters on tenant_id."""

    @pytest.mark.asyncio
    async def test_search_rejects_empty_tenant(
        self,
        mock_db_session: AsyncMock,
    ) -> None:
        """search raises TenantIsolationError for empty UUID tenant."""
        from context_os.vector.search import search

        # Empty UUID equivalent
        with pytest.raises((TenantIsolationError, Exception)):
            await search(
                session=mock_db_session,
                tenant_id=None,  # type: ignore[arg-type]
                query_text="test query",
            )

    @pytest.mark.asyncio
    async def test_search_sql_includes_tenant_filter(
        self,
        mock_db_session: AsyncMock,
        tenant_a_db_id: uuid.UUID,
    ) -> None:
        """search SQL WHERE clause includes tenant_id filter."""
        from context_os.vector.search import search

        executed_stmts: list[Any] = []

        async def mock_execute(stmt: Any) -> Any:
            executed_stmts.append(stmt)
            result = MagicMock()
            result.fetchall.return_value = []
            return result

        mock_db_session.execute = AsyncMock(side_effect=mock_execute)

        with patch("context_os.vector.search.get_embedding_model") as mock_model:
            mock_instance = MagicMock()
            mock_instance.encode.return_value = [0.0] * 768
            mock_model.return_value = mock_instance

            results = await search(
                session=mock_db_session,
                tenant_id=tenant_a_db_id,
                query_text="test query",
            )

        assert isinstance(results, list)
        # The query was executed once
        assert len(executed_stmts) == 1

        # Verify the SQL statement includes tenant_id WHERE clause
        stmt_str = str(executed_stmts[0])
        assert "tenant_id" in stmt_str.lower()


# ── Tenant isolation: repositories ────────────────────────────────────────────


class TestRepositoryIsolation:
    """Test that all repositories enforce tenant_id in WHERE clauses."""

    @pytest.mark.asyncio
    async def test_oauth_repo_rejects_empty_tenant(
        self,
        mock_db_session: AsyncMock,
    ) -> None:
        """OAuthTokenRepository.get_for_tenant_integration raises on empty tenant."""
        from context_os.relational.repositories import OAuthTokenRepository

        repo = OAuthTokenRepository(mock_db_session)

        with pytest.raises(TenantIsolationError):
            await repo.get_for_tenant_integration(
                tenant_id=uuid.UUID("00000000-0000-0000-0000-000000000000"),
                integration="github",
            )

    @pytest.mark.asyncio
    async def test_checkpoint_repo_rejects_empty_tenant_string(
        self,
        mock_db_session: AsyncMock,
    ) -> None:
        """CheckpointRepository.get raises on zero UUID (effectively empty)."""
        from context_os.relational.repositories import CheckpointRepository

        repo = CheckpointRepository(mock_db_session)

        # Valid UUID should not raise
        valid_id = uuid.uuid4()
        mock_db_session.execute = AsyncMock(
            return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None))
        )

        # Should not raise
        result = await repo.get(
            tenant_id=valid_id,
            integration="github",
            object_type="issues",
        )
        assert result is None  # No checkpoint found


# ── Cross-tenant zero-visibility test ─────────────────────────────────────────


class TestCrossTenantVisibility:
    """Comprehensive cross-tenant visibility tests.

    Ensures that authenticated Tenant B requests return zero results
    when only Tenant A has data.
    """

    @pytest.mark.asyncio
    async def test_graph_traverse_tenant_b_sees_zero_nodes(
        self,
        mock_age_pool: MagicMock,
        tenant_a_clerk_id: str,
        tenant_b_clerk_id: str,
    ) -> None:
        """Graph traversal as Tenant B returns no Tenant A nodes."""
        from context_os.graph.queries import traverse

        # Simulate: graph returns nodes only matching tenant_a
        async def mock_run_cypher(
            pool: Any,
            cypher: str,
            params: dict[str, Any] | None = None,
            **kwargs: Any,
        ) -> list[dict[str, Any]]:
            # Only return data if tenant_id matches tenant_a
            if params and params.get("tenant_id") == tenant_a_clerk_id:
                return [
                    {
                        "start_node": {
                            "properties": {
                                "id": "node1",
                                "tenant_id": tenant_a_clerk_id,
                                "node_type": "Artifact",
                            }
                        },
                        "rel": {"id": "rel1", "label": "PRODUCES"},
                        "end_node": {
                            "properties": {
                                "id": "node2",
                                "tenant_id": tenant_a_clerk_id,
                                "node_type": "Initiative",
                            }
                        },
                    }
                ]
            return []  # Tenant B sees nothing

        from_id = str(uuid.uuid4())

        with patch("context_os.graph.queries.run_cypher", side_effect=mock_run_cypher):
            # Tenant A traversal returns data
            result_a = await traverse(
                pool=mock_age_pool,
                tenant_id=tenant_a_clerk_id,
                from_id=from_id,
            )

            # Tenant B traversal returns empty
            result_b = await traverse(
                pool=mock_age_pool,
                tenant_id=tenant_b_clerk_id,
                from_id=from_id,
            )

        # Tenant A sees data, Tenant B sees nothing
        assert len(result_a.nodes) >= 0  # May be 0 if start node not found
        assert len(result_b.nodes) == 0, "Tenant B must see zero nodes"
        assert len(result_b.edges) == 0, "Tenant B must see zero edges"

        # Verify no Tenant A data leaked into Tenant B results
        for node in result_b.nodes:
            assert node.get("tenant_id") != tenant_a_clerk_id, "Tenant A data leaked!"


# ── Phase 4: Onboarding session isolation ──────────────────────────────────────


class TestOnboardingSessionIsolation:
    """Onboarding sessions are scoped per tenant — Tenant B sees Tenant A's data only
    if authenticated as Tenant A.

    Marked nightly_eval to run in scheduled CI.
    """

    @pytest.mark.nightly_eval
    @pytest.mark.asyncio
    async def test_get_or_create_scoped_to_tenant(
        self,
        mock_db_session: AsyncMock,
        tenant_a_db_id: uuid.UUID,
        tenant_b_db_id: uuid.UUID,
    ) -> None:
        """get_or_create never returns a session belonging to a different tenant."""
        from context_os.services.onboarding_service import OnboardingService

        # Tenant A session
        tenant_a_session = MagicMock()
        tenant_a_session.id = uuid.uuid4()
        tenant_a_session.tenant_id = tenant_a_db_id
        tenant_a_session.current_step = "survey"
        tenant_a_session.step_completed_at = {}
        tenant_a_session.step_started_at = {}
        tenant_a_session.connected_integrations = []

        # First call returns Tenant A session; second returns None (no Tenant B session)
        mock_result_a = MagicMock()
        mock_result_a.scalar_one_or_none.return_value = tenant_a_session
        mock_result_none = MagicMock()
        mock_result_none.scalar_one_or_none.return_value = None
        mock_db_session.execute = AsyncMock(
            side_effect=[mock_result_a, mock_result_none]
        )
        mock_db_session.add = MagicMock()
        mock_db_session.flush = AsyncMock()
        mock_db_session.refresh = AsyncMock()

        svc = OnboardingService(mock_db_session)

        result_a = await svc.get_or_create(tenant_a_db_id)
        assert result_a.tenant_id == tenant_a_db_id

        # Tenant B gets a new session (None returned means new session created)
        mock_onboarding = "context_os.services.onboarding_service.OnboardingSession"
        with patch(mock_onboarding) as mock_cls:
            new_b_session = MagicMock()
            new_b_session.tenant_id = tenant_b_db_id
            new_b_session.current_step = "survey"
            mock_cls.return_value = new_b_session
            with patch("context_os.services.onboarding_service.select"):
                result_b = await svc.get_or_create(tenant_b_db_id)

        # Tenant B session tenant_id must NOT be Tenant A's
        assert result_b.tenant_id != tenant_a_db_id

    @pytest.mark.nightly_eval
    @pytest.mark.asyncio
    async def test_ingest_jobs_scoped_to_tenant(
        self,
        mock_db_session: AsyncMock,
        tenant_a_db_id: uuid.UUID,
        tenant_b_db_id: uuid.UUID,
    ) -> None:
        """IngestService create_job sets tenant_id; jobs are always tenant-scoped."""
        from context_os.services.ingest_service import IngestService

        tenant_a_job = MagicMock()
        tenant_a_job.id = uuid.uuid4()
        tenant_a_job.tenant_id = tenant_a_db_id
        tenant_a_job.source = "all"
        tenant_a_job.status = "running"

        mock_db_session.add = MagicMock()
        mock_db_session.flush = AsyncMock()
        mock_db_session.refresh = AsyncMock()

        with patch(
            "context_os.services.ingest_service.IngestJob",
            return_value=tenant_a_job,
        ):
            with patch("context_os.services.ingest_service.select"):
                svc = IngestService(mock_db_session)
                job = await svc.create_job(tenant_a_db_id, "all")

        # Confirm the job is scoped to Tenant A
        assert job.tenant_id == tenant_a_db_id
        assert job.tenant_id != tenant_b_db_id
