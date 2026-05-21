"""Unit tests for admin funnel query logic.

Validates funnel row computation, drop-off flag logic, and timing segments.
DB session is mocked.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock


def _make_onboarding_row(
    tenant_id: uuid.UUID | None = None,
    current_step: str = "connect",
    updated_at: datetime | None = None,
    step_completed_at: dict | None = None,
    step_started_at: dict | None = None,
    tenant_name: str = "Acme Corp",
) -> MagicMock:
    """Build a mock row as returned by the funnel JOIN query."""
    row = MagicMock()
    row.tenant_id = tenant_id or uuid.uuid4()
    row.tenant_name = tenant_name
    row.current_step = current_step
    row.updated_at = updated_at or datetime.now(UTC)
    row.step_completed_at = step_completed_at or {}
    row.step_started_at = step_started_at or {}
    row.signup_to_connect_ms = None
    row.connect_to_ingest_ms = None
    row.ingest_to_briefing_ms = None
    row.total_active_attention_ms = None
    return row


class TestAdminFunnelQuery:
    async def test_funnel_returns_correct_current_step(self) -> None:
        """Funnel query returns the correct current_step per org."""
        from context_os.api.admin_funnel import build_funnel_rows

        rows = [
            _make_onboarding_row(current_step="survey"),
            _make_onboarding_row(current_step="connect"),
        ]
        result = build_funnel_rows(rows)
        steps = [r.current_step for r in result]
        assert "survey" in steps
        assert "connect" in steps

    async def test_drop_off_flag_true_when_stuck_over_48h(self) -> None:
        """drop_off_flag=True when org is not 'activated' and stuck > 48 hours."""
        from context_os.api.admin_funnel import build_funnel_rows

        old_time = datetime.now(UTC) - timedelta(hours=50)
        rows = [_make_onboarding_row(current_step="connect", updated_at=old_time)]

        result = build_funnel_rows(rows)
        assert result[0].drop_off_flag is True

    async def test_drop_off_flag_false_when_activated(self) -> None:
        """drop_off_flag=False even if updated_at is old when step is 'activated'."""
        from context_os.api.admin_funnel import build_funnel_rows

        old_time = datetime.now(UTC) - timedelta(hours=100)
        rows = [_make_onboarding_row(current_step="activated", updated_at=old_time)]

        result = build_funnel_rows(rows)
        assert result[0].drop_off_flag is False

    async def test_timing_segments_none_for_non_activated(self) -> None:
        """Timing segment fields are None for orgs that have not reached 'activated'."""
        from context_os.api.admin_funnel import build_funnel_rows

        rows = [_make_onboarding_row(current_step="ingest")]
        result = build_funnel_rows(rows)

        row = result[0]
        assert row.signup_to_connect_ms is None
        assert row.connect_to_ingest_ms is None
