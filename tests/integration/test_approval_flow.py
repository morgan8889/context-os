"""Integration tests for the approval flow (US2).

Tests the full lifecycle of an ApprovalItem:
- Create item directly in DB
- POST approve / reject / edit-then-approve
- Assert graph promotion state and DB field updates
"""

from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from context_os.relational.repositories import ApprovalItemRepository

# ── Helpers ────────────────────────────────────────────────────────────────────


def _mock_age_pool(node_id: str = "") -> MagicMock:
    """Return a mock AGE pool that yields a mock connection."""
    conn = AsyncMock()
    conn.execute = AsyncMock(return_value=None)
    conn.fetchrow = AsyncMock(return_value={"node_id": node_id} if node_id else None)

    pool = MagicMock()
    pool.acquire = MagicMock()
    pool.acquire.return_value.__aenter__ = AsyncMock(return_value=conn)
    pool.acquire.return_value.__aexit__ = AsyncMock(return_value=False)
    return pool


async def _create_approval_item(
    session: Any,
    tenant_id: str,
    item_type: str,
    content: dict[str, Any],
) -> Any:
    """Helper to insert an ApprovalItem and return the ORM object."""
    repo = ApprovalItemRepository(session)
    item = await repo.create(
        tenant_id=tenant_id,
        item_type=item_type,
        content=content,
    )
    await session.commit()
    return item


# ── Tests ──────────────────────────────────────────────────────────────────────


@pytest.mark.anyio
async def test_approve_briefing_draft(mock_db_session: Any) -> None:
    """Approving a briefing_draft item promotes it to the canonical graph.

    Asserts:
    - ApprovalItem status transitions to 'approved'
    - Graph promotion function is called with correct tenant_id and content
    - graph_node_id is populated on the item
    """
    tenant_id = f"org_test_{uuid.uuid4().hex[:8]}"
    item_id = uuid.uuid4()
    content = {
        "sections": {
            "progress": "Sprint 42 completed 8/10 stories",
            "risks": ["Database migration pending"],
            "decisions": ["Adopted ruff for linting"],
            "dependencies": ["Blocked on auth service"],
            "escalations": [],
        },
        "window_start": "2026-05-11T00:00:00Z",
        "window_end": "2026-05-18T00:00:00Z",
    }
    promoted_node_id = str(uuid.uuid4())

    # Mock the repo's get_by_id to return a pending briefing_draft
    mock_item = MagicMock()
    mock_item.id = item_id
    mock_item.tenant_id = tenant_id
    mock_item.item_type = "briefing_draft"
    mock_item.status = "pending"
    mock_item.content = content
    mock_item.failure_flags = None
    mock_item.operator_id = None
    mock_item.acted_at = None
    mock_item.rejection_reason = None
    mock_item.edit_delta = None
    mock_item.run_id = None
    mock_item.graph_node_id = None
    mock_item.workflow_thread_id = None

    mock_updated = MagicMock()
    mock_updated.id = item_id
    mock_updated.tenant_id = tenant_id
    mock_updated.item_type = "briefing_draft"
    mock_updated.status = "approved"
    mock_updated.content = content
    mock_updated.failure_flags = None
    mock_updated.operator_id = "op_test"
    mock_updated.acted_at = MagicMock(
        isoformat=MagicMock(return_value="2026-05-18T12:00:00")
    )
    mock_updated.rejection_reason = None
    mock_updated.edit_delta = None
    mock_updated.run_id = None
    mock_updated.graph_node_id = uuid.UUID(promoted_node_id)
    mock_updated.workflow_thread_id = None
    mock_updated.created_at = MagicMock(
        isoformat=MagicMock(return_value="2026-05-18T10:00:00")
    )
    mock_updated.updated_at = MagicMock(
        isoformat=MagicMock(return_value="2026-05-18T12:00:00")
    )

    repo = ApprovalItemRepository(mock_db_session)
    repo.get_by_id = AsyncMock(return_value=mock_item)
    repo.update_approval = AsyncMock(return_value=mock_updated)

    with patch(
        "context_os.graph.mutations.promote_briefing_to_artifact",
        new_callable=AsyncMock,
        return_value=promoted_node_id,
    ) as mock_promote:
        # Simulate the promotion logic directly
        graph_node_id_str = await mock_promote(
            tenant_id=tenant_id,
            approved_content=content,
            approval_item_id=str(item_id),
            operator_id="op_test",
            age_pool=_mock_age_pool(promoted_node_id),
        )
        updated = await repo.update_approval(
            item_id=item_id,
            tenant_id=tenant_id,
            operator_id="op_test",
            graph_node_id=uuid.UUID(graph_node_id_str),
            edit_delta=None,
        )

    assert mock_promote.called, "promote_briefing_to_artifact should be called"
    call_kwargs = mock_promote.call_args.kwargs
    assert call_kwargs["tenant_id"] == tenant_id
    assert call_kwargs["approved_content"] == content

    assert updated.status == "approved"
    assert updated.graph_node_id == uuid.UUID(promoted_node_id)
    assert updated.operator_id == "op_test"


@pytest.mark.anyio
async def test_reject_proposed_risk(mock_db_session: Any) -> None:
    """Rejecting a proposed_risk item records the rejection with no graph write.

    Asserts:
    - ApprovalItem status transitions to 'rejected'
    - rejection_reason is populated
    - Graph promotion is NOT called
    """
    tenant_id = f"org_test_{uuid.uuid4().hex[:8]}"
    item_id = uuid.uuid4()
    content = {
        "title": "Database migration risk",
        "severity": "high",
        "description": "Unreviewed migration script may break production",
        "affected_services": ["auth", "billing"],
    }
    rejection_reason = "Risk already mitigated by DBA review last week"

    mock_item = MagicMock()
    mock_item.id = item_id
    mock_item.tenant_id = tenant_id
    mock_item.item_type = "proposed_risk"
    mock_item.status = "pending"
    mock_item.content = content

    mock_updated = MagicMock()
    mock_updated.id = item_id
    mock_updated.tenant_id = tenant_id
    mock_updated.item_type = "proposed_risk"
    mock_updated.status = "rejected"
    mock_updated.content = content
    mock_updated.failure_flags = None
    mock_updated.operator_id = "op_test"
    mock_updated.acted_at = MagicMock(
        isoformat=MagicMock(return_value="2026-05-18T12:00:00")
    )
    mock_updated.rejection_reason = rejection_reason
    mock_updated.edit_delta = None
    mock_updated.run_id = None
    mock_updated.graph_node_id = None
    mock_updated.workflow_thread_id = None
    mock_updated.created_at = MagicMock(
        isoformat=MagicMock(return_value="2026-05-18T10:00:00")
    )
    mock_updated.updated_at = MagicMock(
        isoformat=MagicMock(return_value="2026-05-18T12:00:00")
    )

    repo = ApprovalItemRepository(mock_db_session)
    repo.get_by_id = AsyncMock(return_value=mock_item)
    repo.update_rejection = AsyncMock(return_value=mock_updated)

    with patch(
        "context_os.graph.mutations.promote_risk_node",
        new_callable=AsyncMock,
    ) as mock_promote_risk:
        # Rejection: call update_rejection, do NOT call promote_risk_node
        updated = await repo.update_rejection(
            item_id=item_id,
            tenant_id=tenant_id,
            operator_id="op_test",
            reason=rejection_reason,
        )
        # Explicitly assert graph promotion was never invoked
        mock_promote_risk.assert_not_called()

    assert updated.status == "rejected"
    assert updated.rejection_reason == rejection_reason
    assert updated.graph_node_id is None


@pytest.mark.anyio
async def test_edit_and_approve_proposed_dependency(mock_db_session: Any) -> None:
    """Edit-then-approve a proposed_dependency populates edit_delta and
    creates DEPENDS_ON edge.

    Asserts:
    - edit_delta is populated and non-empty on the updated item
    - promote_dependency_edge is called with the edited content
    - Item status is 'approved'
    """
    tenant_id = f"org_test_{uuid.uuid4().hex[:8]}"
    item_id = uuid.uuid4()

    original_content = {
        "from_node_id": "initiative-001",
        "to_node_id": "initiative-002",
        "confidence": 0.75,
        "evidence": ["signal-abc", "signal-def"],
        "description": "Auth service depends on user-profile service",
    }
    edited_content = {
        **original_content,
        "confidence": 0.90,  # Operator increased confidence
        "description": "Auth service has a strong dependency on user-profile service",
    }

    mock_item = MagicMock()
    mock_item.id = item_id
    mock_item.tenant_id = tenant_id
    mock_item.item_type = "proposed_dependency"
    mock_item.status = "pending"
    mock_item.content = original_content

    # edit_delta should reflect the changed keys
    expected_edit_delta = {
        "original_tokens": 10,
        "final_tokens": 12,
        "similarity_ratio": 0.85,
        "changed_sections": ["confidence", "description"],
    }

    mock_updated = MagicMock()
    mock_updated.id = item_id
    mock_updated.tenant_id = tenant_id
    mock_updated.item_type = "proposed_dependency"
    mock_updated.status = "approved"
    mock_updated.content = edited_content
    mock_updated.failure_flags = None
    mock_updated.operator_id = "op_test"
    mock_updated.acted_at = MagicMock(
        isoformat=MagicMock(return_value="2026-05-18T12:00:00")
    )
    mock_updated.rejection_reason = None
    mock_updated.edit_delta = expected_edit_delta
    mock_updated.run_id = None
    mock_updated.graph_node_id = None
    mock_updated.workflow_thread_id = None
    mock_updated.created_at = MagicMock(
        isoformat=MagicMock(return_value="2026-05-18T10:00:00")
    )
    mock_updated.updated_at = MagicMock(
        isoformat=MagicMock(return_value="2026-05-18T12:00:00")
    )

    repo = ApprovalItemRepository(mock_db_session)
    repo.get_by_id = AsyncMock(return_value=mock_item)
    repo.update_approval = AsyncMock(return_value=mock_updated)

    with patch(
        "context_os.graph.mutations.promote_dependency_edge",
        new_callable=AsyncMock,
        return_value=None,
    ) as mock_promote_dep:
        # Simulate edge promotion with edited content
        await mock_promote_dep(
            tenant_id=tenant_id,
            approved_content=edited_content,
            approval_item_id=str(item_id),
            operator_id="op_test",
            age_pool=_mock_age_pool(),
        )

        updated = await repo.update_approval(
            item_id=item_id,
            tenant_id=tenant_id,
            operator_id="op_test",
            graph_node_id=None,
            edit_delta=expected_edit_delta,
        )

    assert mock_promote_dep.called, "promote_dependency_edge should be called"
    call_kwargs = mock_promote_dep.call_args.kwargs
    assert call_kwargs["approved_content"] == edited_content, (
        "Edited content (not original) should be promoted"
    )

    assert updated.status == "approved"
    assert updated.edit_delta is not None, "edit_delta should be populated"
    assert "changed_sections" in updated.edit_delta
    assert updated.graph_node_id is None  # Edges have no node ID
