"""Initial schema: tenants, oauth_tokens, sync_checkpoints, node_embeddings.

Revision ID: 0001
Revises: (none)
Create Date: 2026-05-18
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create all Phase 1 tables with correct constraints and indexes."""

    # Enable required extensions (idempotent)
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # ── tenants ────────────────────────────────────────────────────────────────
    op.create_table(
        "tenants",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("clerk_org_id", sa.TEXT(), nullable=False),
        sa.Column("name", sa.TEXT(), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("clerk_org_id", name="uq_tenants_clerk_org_id"),
    )

    # ── oauth_tokens ────────────────────────────────────────────────────────────
    op.create_table(
        "oauth_tokens",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("tenant_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("integration", sa.TEXT(), nullable=False),
        sa.Column("access_token_enc", sa.LargeBinary(), nullable=False),
        sa.Column("refresh_token_enc", sa.LargeBinary(), nullable=True),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("scope", sa.TEXT(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "tenant_id",
            "integration",
            name="uq_oauth_tokens_tenant_integration",
        ),
    )

    # ── sync_checkpoints ────────────────────────────────────────────────────────
    op.create_table(
        "sync_checkpoints",
        sa.Column("tenant_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("integration", sa.TEXT(), nullable=False),
        sa.Column("object_type", sa.TEXT(), nullable=False),
        sa.Column("cursor_value", sa.TEXT(), nullable=True),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "tenant_id",
            "integration",
            "object_type",
            name="pk_sync_checkpoints",
        ),
    )

    # ── node_embeddings ─────────────────────────────────────────────────────────
    op.create_table(
        "node_embeddings",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("node_type", sa.TEXT(), nullable=False),
        sa.Column("content", sa.TEXT(), nullable=False),
        # vector(768) column for all-mpnet-base-v2 embeddings
        sa.Column(
            "embedding",
            sa.Text(),  # placeholder; actual Vector(768) via raw SQL below
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            ondelete="CASCADE",
        ),
    )

    # Add proper vector column type (pgvector) — alter after table creation
    op.execute(
        "ALTER TABLE node_embeddings"
        " ALTER COLUMN embedding TYPE vector(768) USING NULL::vector(768)"
    )

    # HNSW index for fast approximate cosine similarity search
    op.execute(
        "CREATE INDEX ON node_embeddings USING hnsw (embedding vector_cosine_ops) "
        "WITH (m=16, ef_construction=64)"
    )


def downgrade() -> None:
    """Drop all Phase 1 tables in reverse dependency order."""
    op.drop_table("node_embeddings")
    op.drop_table("sync_checkpoints")
    op.drop_table("oauth_tokens")
    op.drop_table("tenants")
