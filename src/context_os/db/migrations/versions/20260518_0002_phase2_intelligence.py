"""Phase 2 Intelligence: approval_items, briefing_runs, eval_runs, golden_datasets.

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-18
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create all Phase 2 tables with correct constraints and indexes."""

    # ── approval_items ──────────────────────────────────────────────────────────
    # Stores all pending, approved, and rejected agent-generated outputs.
    # tenant_id is TEXT (Clerk org ID) rather than UUID — matches AGE graph scoping.
    op.create_table(
        "approval_items",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("tenant_id", sa.TEXT(), nullable=False),
        sa.Column("item_type", sa.TEXT(), nullable=False),
        sa.Column(
            "status",
            sa.TEXT(),
            nullable=False,
            server_default=sa.text("'pending'"),
        ),
        sa.Column("content", postgresql.JSONB(), nullable=False),
        sa.Column("failure_flags", postgresql.JSONB(), nullable=True),
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
        sa.Column("operator_id", sa.TEXT(), nullable=True),
        sa.Column("acted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("rejection_reason", sa.TEXT(), nullable=True),
        sa.Column("edit_delta", postgresql.JSONB(), nullable=True),
        sa.Column("stale_notified_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("graph_node_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("workflow_thread_id", sa.TEXT(), nullable=True),
    )
    op.create_index(
        "ix_approval_items_tenant_status",
        "approval_items",
        ["tenant_id", "status"],
    )
    op.create_index(
        "ix_approval_items_tenant_created",
        "approval_items",
        ["tenant_id", sa.text("created_at DESC")],
    )
    op.create_index(
        "ix_approval_items_run_id",
        "approval_items",
        ["run_id"],
        postgresql_where=sa.text("run_id IS NOT NULL"),
    )

    # ── briefing_runs ───────────────────────────────────────────────────────────
    op.create_table(
        "briefing_runs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("tenant_id", sa.TEXT(), nullable=False),
        sa.Column("trigger_type", sa.TEXT(), nullable=False),
        sa.Column(
            "window_days",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("7"),
        ),
        sa.Column("window_start", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("window_end", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column(
            "status",
            sa.TEXT(),
            nullable=False,
            server_default=sa.text("'generating'"),
        ),
        sa.Column("input_signal_counts", postgresql.JSONB(), nullable=True),
        sa.Column("retrieval_hit_rate", sa.Numeric(4, 3), nullable=True),
        sa.Column("cost_tokens", sa.Integer(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("error_detail", sa.TEXT(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("approval_item_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index(
        "ix_briefing_runs_tenant",
        "briefing_runs",
        ["tenant_id", sa.text("created_at DESC")],
    )

    # ── eval_runs ───────────────────────────────────────────────────────────────
    op.create_table(
        "eval_runs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("tenant_id", sa.TEXT(), nullable=False),
        sa.Column("eval_type", sa.TEXT(), nullable=False),
        sa.Column("dataset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("dataset_version", sa.TEXT(), nullable=False),
        sa.Column(
            "status",
            sa.TEXT(),
            nullable=False,
            server_default=sa.text("'running'"),
        ),
        sa.Column(
            "scores",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'"),
        ),
        sa.Column("gates_passed", sa.Boolean(), nullable=True),
        sa.Column("compared_to_run_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("score_deltas", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("error_detail", sa.TEXT(), nullable=True),
    )
    op.create_index(
        "ix_eval_runs_tenant_type",
        "eval_runs",
        ["tenant_id", "eval_type", sa.text("created_at DESC")],
    )

    # ── golden_datasets ─────────────────────────────────────────────────────────
    op.create_table(
        "golden_datasets",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("tenant_id", sa.TEXT(), nullable=False),
        sa.Column("dataset_type", sa.TEXT(), nullable=False),
        sa.Column("version", sa.TEXT(), nullable=False),
        sa.Column("description", sa.TEXT(), nullable=True),
        sa.Column("record_count", sa.Integer(), nullable=False),
        sa.Column("content", postgresql.JSONB(), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("built_from_approval_items", postgresql.JSONB(), nullable=True),
        sa.UniqueConstraint(
            "tenant_id",
            "dataset_type",
            "version",
            name="uq_golden_datasets_tenant_type_version",
        ),
    )


def downgrade() -> None:
    """Drop all Phase 2 tables in reverse dependency order."""
    op.drop_table("golden_datasets")
    op.drop_table("eval_runs")
    op.drop_table("briefing_runs")
    op.drop_index("ix_approval_items_run_id", table_name="approval_items")
    op.drop_index("ix_approval_items_tenant_created", table_name="approval_items")
    op.drop_index("ix_approval_items_tenant_status", table_name="approval_items")
    op.drop_table("approval_items")
