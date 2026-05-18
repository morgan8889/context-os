"""SQLAlchemy ORM declarative models for Context-OS relational tables.

These tables handle operational state (tenants, OAuth tokens, sync checkpoints,
and vector embeddings mirror). Graph data lives in Apache AGE.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    JSON,
    TEXT,
    TIMESTAMP,
    Boolean,
    ForeignKey,
    Integer,
    LargeBinary,
    Numeric,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""

    pass


class Tenant(Base):
    """Registered tenants (Clerk organizations).

    Each tenant corresponds to a Clerk organization. The clerk_org_id is the
    primary correlation key between Clerk JWTs and database records.
    """

    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    clerk_org_id: Mapped[str] = mapped_column(
        TEXT,
        unique=True,
        nullable=False,
        doc="Clerk organization ID from JWT o.id claim",
    )
    name: Mapped[str] = mapped_column(TEXT, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )


class OAuthToken(Base):
    """Encrypted OAuth tokens per tenant per integration.

    Tokens are encrypted with Fernet AES-256 before storage. The metadata
    JSONB column holds integration-specific context (cloudId for Jira,
    installation_id for GitHub, etc.).
    """

    __tablename__ = "oauth_tokens"
    __table_args__ = (UniqueConstraint("tenant_id", "integration"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    integration: Mapped[str] = mapped_column(
        TEXT,
        nullable=False,
        doc="Integration name: github | jira | slack",
    )
    access_token_enc: Mapped[bytes] = mapped_column(
        LargeBinary,
        nullable=False,
        doc="Fernet-encrypted access token bytes",
    )
    refresh_token_enc: Mapped[bytes | None] = mapped_column(
        LargeBinary,
        nullable=True,
        doc="Fernet-encrypted refresh token bytes (nullable)",
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
    )
    scope: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    metadata_: Mapped[dict[str, object] | None] = mapped_column(
        "metadata",
        JSON,
        nullable=True,
        doc="Integration-specific metadata (cloudId, installation_id, etc.)",
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()"),
        onupdate=lambda: datetime.now(UTC),
    )


class SyncCheckpoint(Base):
    """Incremental sync cursors per (tenant, integration, object_type).

    Checkpoint is ONLY updated after a successful DB commit — never after
    a fetch or normalize step. This ensures we can resume without
    re-processing already-committed data.
    """

    __tablename__ = "sync_checkpoints"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        primary_key=True,
    )
    integration: Mapped[str] = mapped_column(
        TEXT,
        primary_key=True,
        doc="Integration name: github | jira | slack",
    )
    object_type: Mapped[str] = mapped_column(
        TEXT,
        primary_key=True,
        doc="Object type: issues | prs | messages | projects | etc.",
    )
    cursor_value: Mapped[str | None] = mapped_column(
        TEXT,
        nullable=True,
        doc="ISO timestamp, nextPageToken, or Slack ts for incremental sync",
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()"),
        onupdate=lambda: datetime.now(UTC),
    )


class NodeEmbedding(Base):
    """Vector embeddings for Artifact and Memory nodes.

    This table mirrors graph nodes that require semantic search. The id
    column matches the UUID used as the node id in the AGE graph.
    """

    __tablename__ = "node_embeddings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        doc="Same UUID as the AGE graph node id",
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    node_type: Mapped[str] = mapped_column(
        TEXT,
        nullable=False,
        doc="Artifact | Memory",
    )
    content: Mapped[str] = mapped_column(
        TEXT,
        nullable=False,
        doc="Text that was embedded (title + body or summary)",
    )
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(768),
        nullable=True,
        doc="all-mpnet-base-v2 768-dimensional embedding",
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()"),
        onupdate=lambda: datetime.now(UTC),
    )


class ApprovalItem(Base):
    """Pending, approved, and rejected agent-generated outputs awaiting operator review.

    All agent outputs live here until an operator approves or rejects them.
    Approved items are promoted to the canonical AGE graph; rejected items
    remain as a provenance log with graph_node_id=None.

    item_type discriminator values:
        'briefing_draft'       — Synthesizer weekly briefing draft
        'proposed_dependency'  — Dependency Mapper proposed DEPENDS_ON edge
        'proposed_risk'        — Synthesizer-detected Risk node
    """

    __tablename__ = "approval_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    tenant_id: Mapped[str] = mapped_column(
        TEXT,
        nullable=False,
        doc="Clerk org ID — scopes all queries",
    )
    item_type: Mapped[str] = mapped_column(
        TEXT,
        nullable=False,
        doc="briefing_draft | proposed_dependency | proposed_risk",
    )
    status: Mapped[str] = mapped_column(
        TEXT,
        nullable=False,
        server_default=text("'pending'"),
        doc="pending | approved | rejected",
    )
    content: Mapped[dict[str, object]] = mapped_column(
        JSONB,
        nullable=False,
        doc="Item-type-specific payload (see data-model.md)",
    )
    failure_flags: Mapped[dict[str, object] | None] = mapped_column(
        JSONB,
        nullable=True,
        doc="List of {type, detail} detected failure modes from failure_detection.py",
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()"),
        onupdate=lambda: datetime.now(UTC),
    )
    operator_id: Mapped[str | None] = mapped_column(
        TEXT,
        nullable=True,
        doc="Clerk user ID of the operator who acted on this item",
    )
    acted_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
        doc="Timestamp of approve or reject action",
    )
    rejection_reason: Mapped[str | None] = mapped_column(
        TEXT,
        nullable=True,
        doc="Operator-supplied reason when rejecting",
    )
    edit_delta: Mapped[dict[str, object] | None] = mapped_column(
        JSONB,
        nullable=True,
        doc="{original_tokens, final_tokens, changed_sections[]} on edit-approve",
    )
    stale_notified_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
        doc="When stale notification was sent (if any)",
    )
    run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        doc="FK to briefing_runs.id for briefing_draft items",
    )
    graph_node_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        doc="Populated after approve → graph promotion (NULL for edge-only items)",
    )
    workflow_thread_id: Mapped[str | None] = mapped_column(
        TEXT,
        nullable=True,
        doc="LangGraph thread ID for interrupt/resume workflow",
    )


class BriefingRun(Base):
    """Tracks each briefing generation attempt.

    One BriefingRun produces one ApprovalItem of type briefing_draft.
    Status transitions: generating → complete | failed | partial.
    """

    __tablename__ = "briefing_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    tenant_id: Mapped[str] = mapped_column(
        TEXT,
        nullable=False,
        doc="Clerk org ID",
    )
    trigger_type: Mapped[str] = mapped_column(
        TEXT,
        nullable=False,
        doc="manual | scheduled",
    )
    window_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("7"),
        doc="Number of days in the briefing window",
    )
    window_start: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        doc="Start of the data window for this briefing",
    )
    window_end: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        doc="End of the data window for this briefing",
    )
    status: Mapped[str] = mapped_column(
        TEXT,
        nullable=False,
        server_default=text("'generating'"),
        doc="generating | complete | failed | partial",
    )
    input_signal_counts: Mapped[dict[str, object] | None] = mapped_column(
        JSONB,
        nullable=True,
        doc='{"github": N, "jira": N, "slack": N}',
    )
    retrieval_hit_rate: Mapped[float | None] = mapped_column(
        Numeric(4, 3),
        nullable=True,
        doc="Fraction of retrieval queries returning results",
    )
    cost_tokens: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        doc="Total token count (prompt + completion) for this run",
    )
    latency_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        doc="Milliseconds from trigger to draft-ready",
    )
    error_detail: Mapped[str | None] = mapped_column(
        TEXT,
        nullable=True,
        doc="Error message if status=failed",
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
        doc="When the run reached a terminal state",
    )
    approval_item_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        doc="FK to approval_items.id once the draft is enqueued",
    )


class EvalRun(Base):
    """Stores the result of each evaluation suite execution.

    Both synthesizer and mapper evals share this table, discriminated by eval_type.
    CI gate thresholds: synthesizer accept_rate >= 0.40, mapper recall >= 0.50.
    """

    __tablename__ = "eval_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    tenant_id: Mapped[str] = mapped_column(
        TEXT,
        nullable=False,
        doc="Clerk org ID",
    )
    eval_type: Mapped[str] = mapped_column(
        TEXT,
        nullable=False,
        doc="synthesizer | mapper",
    )
    dataset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        doc="FK to golden_datasets.id",
    )
    dataset_version: Mapped[str] = mapped_column(
        TEXT,
        nullable=False,
        doc="Semantic version of the dataset used (e.g. '1.0.0')",
    )
    status: Mapped[str] = mapped_column(
        TEXT,
        nullable=False,
        server_default=text("'running'"),
        doc="running | passed | failed | error",
    )
    scores: Mapped[dict[str, object]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'"),
        doc="Metric scores keyed by metric name (type-specific shape)",
    )
    gates_passed: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
        doc="True if all CI gates cleared; False if any failed; None while running",
    )
    compared_to_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        doc="FK to eval_runs.id for delta computation (optional)",
    )
    score_deltas: Mapped[dict[str, object] | None] = mapped_column(
        JSONB,
        nullable=True,
        doc="Score deltas vs compared_to_run_id",
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
    )
    duration_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        doc="Total eval run duration in milliseconds",
    )
    error_detail: Mapped[str | None] = mapped_column(
        TEXT,
        nullable=True,
        doc="Error message if status=error",
    )


class GoldenDataset(Base):
    """Versioned reference datasets used as ground truth for eval suites.

    Records are stored as JSONB blobs keyed by eval type:
        synthesizer: list of GoldenRecord dicts
        mapper: list of dependency pair dicts
    """

    __tablename__ = "golden_datasets"
    __table_args__ = (UniqueConstraint("tenant_id", "dataset_type", "version"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    tenant_id: Mapped[str] = mapped_column(
        TEXT,
        nullable=False,
        doc="Clerk org ID",
    )
    dataset_type: Mapped[str] = mapped_column(
        TEXT,
        nullable=False,
        doc="synthesizer | mapper",
    )
    version: Mapped[str] = mapped_column(
        TEXT,
        nullable=False,
        doc="Semantic version string (e.g. '1.0.0')",
    )
    description: Mapped[str | None] = mapped_column(
        TEXT,
        nullable=True,
    )
    record_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Number of records in the content array",
    )
    content: Mapped[dict[str, object]] = mapped_column(
        JSONB,
        nullable=False,
        doc="Array of records (see data-model.md for schema per dataset_type)",
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    built_from_approval_items: Mapped[dict[str, object] | None] = mapped_column(
        JSONB,
        nullable=True,
        doc="List of approval_item UUIDs used to build this dataset",
    )
