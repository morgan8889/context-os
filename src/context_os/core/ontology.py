"""Core domain ontology: node types, edge types, and base schemas.

All graph nodes must conform to BaseNodeSchema. All queries filter on tenant_id.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class NodeType(StrEnum):
    """Canonical node types for the Context-OS memory graph."""

    Goal = "Goal"
    Initiative = "Initiative"
    Signal = "Signal"
    Artifact = "Artifact"
    Actor = "Actor"
    Memory = "Memory"


class EdgeType(StrEnum):
    """Canonical edge labels for the Context-OS memory graph."""

    IMPLEMENTS = "IMPLEMENTS"
    PRODUCES = "PRODUCES"
    EMITS = "EMITS"
    AUTHORED_BY = "AUTHORED_BY"
    REVIEWED_BY = "REVIEWED_BY"
    REFERENCES = "REFERENCES"
    DEPENDS_ON = "DEPENDS_ON"
    SUMMARIZES = "SUMMARIZES"


class Source(StrEnum):
    """Integration sources for provenance tracking."""

    github = "github"
    jira = "jira"
    slack = "slack"
    internal = "internal"


class BaseNodeSchema(BaseModel):
    """Base properties present on every node in the memory graph.

    Every node MUST carry these fields. Downstream code that reads or writes
    graph nodes MUST populate all required fields.
    """

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        description="Stable identifier — preserved across incremental syncs",
    )
    tenant_id: str = Field(
        ...,
        description="Clerk org ID — all queries filter on this; never empty",
    )
    source: Source = Field(
        ...,
        description="Integration that produced this node",
    )
    source_id: str = Field(
        ...,
        description=(
            "Vendor-assigned identifier (PR number, issue key, message ts, etc.)"
        ),
    )
    fetch_ts: datetime = Field(
        ...,
        description="Timestamp of last successful ingest for this node",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="First time this node was seen in the graph",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Last time this node was updated in the graph",
    )
