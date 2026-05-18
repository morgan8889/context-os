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
    ForeignKey,
    LargeBinary,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
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
