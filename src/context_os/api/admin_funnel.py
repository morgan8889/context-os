"""Admin funnel computation helpers.

Extracted from the admin router so they can be unit-tested without
bringing up the full FastAPI application.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

_DROP_OFF_THRESHOLD = timedelta(hours=48)


@dataclass
class AdminFunnelRow:
    """Single row in the onboarding funnel report.

    Attributes:
        tenant_id: Internal UUID of the tenant.
        tenant_name: Human-readable tenant name.
        current_step: Current onboarding step.
        drop_off_flag: True when the org is stuck (non-activated, >48 h).
        signup_to_connect_ms: Time from signup to first connect (activated only).
        connect_to_ingest_ms: Time from connect to ingest start (activated only).
        ingest_to_briefing_ms: Time from ingest start to briefing (activated only).
        total_active_attention_ms: Sum of active attention time (activated only).
    """

    tenant_id: Any
    tenant_name: str
    current_step: str
    drop_off_flag: bool
    signup_to_connect_ms: int | None
    connect_to_ingest_ms: int | None
    ingest_to_briefing_ms: int | None
    total_active_attention_ms: int | None


def build_funnel_rows(raw_rows: list[Any]) -> list[AdminFunnelRow]:
    """Convert raw DB rows into AdminFunnelRow objects with derived fields.

    Args:
        raw_rows: ORM row objects with fields:
            tenant_id, tenant_name, current_step, updated_at,
            signup_to_connect_ms, connect_to_ingest_ms,
            ingest_to_briefing_ms, total_active_attention_ms.

    Returns:
        List of AdminFunnelRow with drop_off_flag computed.
    """
    now = datetime.now(UTC)
    result: list[AdminFunnelRow] = []

    for row in raw_rows:
        is_activated = row.current_step == "activated"
        updated_at = row.updated_at

        # Ensure updated_at is timezone-aware for comparison
        if updated_at is not None and updated_at.tzinfo is None:
            updated_at = updated_at.replace(tzinfo=UTC)

        drop_off = (
            not is_activated
            and updated_at is not None
            and (now - updated_at) > _DROP_OFF_THRESHOLD
        )

        result.append(
            AdminFunnelRow(
                tenant_id=row.tenant_id,
                tenant_name=row.tenant_name,
                current_step=row.current_step,
                drop_off_flag=drop_off,
                signup_to_connect_ms=(
                    row.signup_to_connect_ms if is_activated else None
                ),
                connect_to_ingest_ms=(
                    row.connect_to_ingest_ms if is_activated else None
                ),
                ingest_to_briefing_ms=(
                    row.ingest_to_briefing_ms if is_activated else None
                ),
                total_active_attention_ms=(
                    row.total_active_attention_ms if is_activated else None
                ),
            )
        )

    return result
