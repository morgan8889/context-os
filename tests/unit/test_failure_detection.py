"""Unit tests for synthesizer failure-mode detection.

Tests use AsyncMock for all graph/repo dependencies to run without a real DB.
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from context_os.agents.synthesizer.failure_detection import (
    detect_citation_error,
    detect_hallucinated_stakeholder,
    detect_stale_dependency,
)

# ── detect_hallucinated_stakeholder ──────────────────────────────────────────


@pytest.mark.anyio
async def test_detect_hallucinated_stakeholder_flags_unknown_name() -> None:
    """Returns FailureFlag when check_actor_exists returns False (name not in graph)."""
    mock_pool = MagicMock()

    with patch(
        "context_os.agents.synthesizer.failure_detection.check_actor_exists",
        new=AsyncMock(return_value=False),
    ):
        flag = await detect_hallucinated_stakeholder(
            name="Ghost McFakename",
            tenant_id="org_test_001",
            age_pool=mock_pool,
        )

    assert flag is not None, "Expected a FailureFlag for an unknown actor name"
    assert flag.flag_type == "hallucinated_stakeholder"
    assert "Ghost McFakename" in flag.detail
    assert flag.severity == "warning"
    assert flag.context.get("cited_name") == "Ghost McFakename"


@pytest.mark.anyio
async def test_detect_hallucinated_stakeholder_passes_known_name() -> None:
    """Returns None when check_actor_exists returns True (name found in graph)."""
    mock_pool = MagicMock()

    with patch(
        "context_os.agents.synthesizer.failure_detection.check_actor_exists",
        new=AsyncMock(return_value=True),
    ):
        flag = await detect_hallucinated_stakeholder(
            name="Alice Engineer",
            tenant_id="org_test_001",
            age_pool=mock_pool,
        )

    assert flag is None, "Expected no FailureFlag for a verified actor name"


# ── detect_stale_dependency ──────────────────────────────────────────────────


@pytest.mark.anyio
async def test_detect_stale_dependency_flags_old_edge() -> None:
    """Returns FailureFlag when the edge is in the stale edges list."""
    mock_pool = MagicMock()
    stale_edge_id = "edge-stale-001"

    with patch(
        "context_os.agents.synthesizer.failure_detection.find_stale_dependencies",
        new=AsyncMock(
            return_value=[
                {"id": stale_edge_id, "updated_at": "2019-01-01"},
                {"id": "edge-other-002", "updated_at": "2018-06-15"},
            ]
        ),
    ):
        flag = await detect_stale_dependency(
            edge_id=stale_edge_id,
            tenant_id="org_test_001",
            age_pool=mock_pool,
        )

    assert flag is not None, "Expected a FailureFlag for a stale dependency edge"
    assert flag.flag_type == "stale_dependency"
    assert stale_edge_id in flag.detail
    assert flag.context.get("edge_id") == stale_edge_id


@pytest.mark.anyio
async def test_detect_stale_dependency_passes_current_edge() -> None:
    """Returns None when the edge is NOT in the stale edges list."""
    mock_pool = MagicMock()

    with patch(
        "context_os.agents.synthesizer.failure_detection.find_stale_dependencies",
        new=AsyncMock(return_value=[]),
    ):
        flag = await detect_stale_dependency(
            edge_id="edge-current-123",
            tenant_id="org_test_001",
            age_pool=mock_pool,
        )

    assert flag is None, "Expected no FailureFlag for a current (non-stale) dependency"


# ── detect_citation_error ────────────────────────────────────────────────────


@pytest.mark.anyio
async def test_detect_citation_error_flags_missing_node_id() -> None:
    """Returns FailureFlag when the cited UUID is not found in node_embeddings."""
    mock_session = AsyncMock()

    # Simulate no row found (scalar_one_or_none returns None)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)

    node_id = str(uuid.uuid4())

    flag = await detect_citation_error(
        source_id=node_id,
        tenant_id="org_test_001",
        session=mock_session,
    )

    assert flag is not None, "Expected a FailureFlag when node not found in embeddings"
    assert flag.flag_type == "citation_error"
    assert node_id in flag.detail
    assert flag.context.get("source_id") == node_id


@pytest.mark.anyio
async def test_detect_citation_error_passes_valid_node_id() -> None:
    """Returns None when the cited UUID exists in node_embeddings."""
    mock_session = AsyncMock()
    node_id = str(uuid.uuid4())

    # Simulate a row found (scalar_one_or_none returns the UUID)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = uuid.UUID(node_id)
    mock_session.execute = AsyncMock(return_value=mock_result)

    flag = await detect_citation_error(
        source_id=node_id,
        tenant_id="org_test_001",
        session=mock_session,
    )

    assert flag is None, "Expected no FailureFlag when node exists in embeddings"


@pytest.mark.anyio
async def test_detect_citation_error_flags_invalid_uuid() -> None:
    """Returns FailureFlag immediately when source_id is not a valid UUID."""
    mock_session = AsyncMock()

    flag = await detect_citation_error(
        source_id="not-a-uuid-at-all",
        tenant_id="org_test_001",
        session=mock_session,
    )

    assert flag is not None, "Expected a FailureFlag for a non-UUID source_id"
    assert flag.flag_type == "citation_error"
    assert "not a valid UUID" in flag.detail
    # Should not have hit the DB
    mock_session.execute.assert_not_called()
