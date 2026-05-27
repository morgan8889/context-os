"""Phase 4 Closed Beta: onboarding_sessions, activation_events, ingest_jobs,
oauth_pending_sessions, revoked_impersonation_tokens; tenant columns.

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-20
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create Phase 4 tables and extend tenants."""

    # ── onboarding_sessions ─────────────────────────────────────────────────────
    op.create_table(
        "onboarding_sessions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "current_step",
            sa.TEXT(),
            nullable=False,
            server_default=sa.text("'survey'"),
        ),
        sa.Column("survey_answer", postgresql.JSONB(), nullable=True),
        sa.Column(
            "connected_integrations",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("scope_selection", postgresql.JSONB(), nullable=True),
        sa.Column("ingest_job_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "step_started_at",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "step_completed_at",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("activated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "ix_onboarding_sessions_tenant_id", "onboarding_sessions", ["tenant_id"]
    )

    # ── activation_events ───────────────────────────────────────────────────────
    op.create_table(
        "activation_events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "occurred_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("signup_to_connect_ms", sa.BIGINT(), nullable=True),
        sa.Column("connect_to_ingest_ms", sa.BIGINT(), nullable=True),
        sa.Column("ingest_to_briefing_ms", sa.BIGINT(), nullable=True),
        sa.Column("total_active_attention_ms", sa.BIGINT(), nullable=True),
        sa.Column(
            "accept_as_is",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "ix_activation_events_tenant_id", "activation_events", ["tenant_id"]
    )

    # ── ingest_jobs ─────────────────────────────────────────────────────────────
    op.create_table(
        "ingest_jobs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("source", sa.TEXT(), nullable=False),
        sa.Column(
            "status",
            sa.TEXT(),
            nullable=False,
            server_default=sa.text("'running'"),
        ),
        sa.Column(
            "progress_pct",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "record_counts",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "started_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("last_record_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("error_detail", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_ingest_jobs_tenant_id", "ingest_jobs", ["tenant_id"])
    op.create_index("ix_ingest_jobs_status", "ingest_jobs", ["status"])

    # ── oauth_pending_sessions ──────────────────────────────────────────────────
    op.create_table(
        "oauth_pending_sessions",
        sa.Column("state", sa.TEXT(), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("source", sa.TEXT(), nullable=False),
        sa.Column("code_verifier", sa.TEXT(), nullable=False),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_oauth_pending_sessions_tenant_id", "oauth_pending_sessions", ["tenant_id"]
    )

    # ── revoked_impersonation_tokens ────────────────────────────────────────────
    op.create_table(
        "revoked_impersonation_tokens",
        sa.Column("jti", sa.TEXT(), primary_key=True),
        sa.Column(
            "revoked_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    # ── extend tenants ──────────────────────────────────────────────────────────
    op.add_column("tenants", sa.Column("beta_cohort_id", sa.TEXT(), nullable=True))
    op.add_column("tenants", sa.Column("onboarded_by", sa.TEXT(), nullable=True))


def downgrade() -> None:
    """Drop Phase 4 tables and revert tenant columns."""
    op.drop_column("tenants", "onboarded_by")
    op.drop_column("tenants", "beta_cohort_id")
    op.drop_table("revoked_impersonation_tokens")
    op.drop_table("oauth_pending_sessions")
    op.drop_table("ingest_jobs")
    op.drop_table("activation_events")
    op.drop_table("onboarding_sessions")
