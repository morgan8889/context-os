"""Structured log schema v1.0.0 for Context-OS.

All application logs MUST conform to this schema. Extension contract:
Phase 2+ MAY add new top-level keys or keys inside metadata.
MUST NOT rename or change types of required fields.
Consumers MUST ignore unknown keys (tolerant reader pattern).
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


class EVENT:
    """Dot-namespaced event vocabulary for Phase 1.

    All event names follow the pattern: {domain}.{action}.{state}
    """

    # ── Ingest events ─────────────────────────────────────────────────────────
    INGEST_RUN_STARTED = "ingest.run.started"
    INGEST_RUN_COMPLETED = "ingest.run.completed"
    INGEST_RUN_CHECKPOINT_SAVED = "ingest.run.checkpoint_saved"
    INGEST_RUN_FAILED = "ingest.run.failed"
    INGEST_SOURCE_RATE_LIMITED = "ingest.source.rate_limited"
    INGEST_SOURCE_TOKEN_EXPIRED = "ingest.source.token_expired"

    # ── Graph events ──────────────────────────────────────────────────────────
    GRAPH_TRAVERSE_EXECUTED = "graph.traverse.executed"
    GRAPH_TRAVERSE_ERROR = "graph.traverse.error"

    # ── Vector events ─────────────────────────────────────────────────────────
    VECTOR_SEARCH_EXECUTED = "vector.search.executed"
    VECTOR_SEARCH_ERROR = "vector.search.error"

    # ── Auth events ───────────────────────────────────────────────────────────
    AUTH_REQUEST_REJECTED = "auth.request.rejected"


@dataclass
class StructuredLogRecord:
    """Structured log record conforming to telemetry schema v1.0.0.

    All fields marked as required MUST be present. Optional fields default
    to sensible values. The metadata field is an open object for extension.

    Attributes:
        timestamp: ISO 8601 UTC timestamp of the log event.
        level: Log level (ERROR|WARN|INFO|DEBUG).
        service: Always "context-os".
        version: Application semver.
        trace_id: OTEL hex trace ID; None if outside span context.
        span_id: OTEL hex span ID; None if outside span context.
        event: Dot-namespaced event name from EVENT constants.
        message: Human-readable description of the event.
        agent_identity: Component or future agent identifier.
        autonomy_level: 0–5 per constitution Principle III.
        tenant_id: Clerk org ID; required for all tenant-scoped events.
        duration_ms: Operation duration in milliseconds.
        metadata: Open dict for event-specific details.
    """

    # Required core fields
    event: str
    message: str
    agent_identity: str
    autonomy_level: int
    tenant_id: str
    duration_ms: float

    # Required with defaults
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    level: str = "INFO"
    service: str = "context-os"
    version: str = "0.1.0"
    trace_id: str | None = None
    span_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a schema-compliant dict."""
        return {
            "timestamp": self.timestamp,
            "level": self.level,
            "service": self.service,
            "version": self.version,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "event": self.event,
            "message": self.message,
            "agent_identity": self.agent_identity,
            "autonomy_level": self.autonomy_level,
            "tenant_id": self.tenant_id,
            "duration_ms": self.duration_ms,
            "metadata": self.metadata,
        }


def emit_structured_log(record: StructuredLogRecord) -> None:
    """Serialize a StructuredLogRecord to JSON and write to stdout.

    The log line is terminated with a newline and flushed immediately
    for container/log-collector compatibility.

    Args:
        record: The structured log record to emit.
    """
    log_line = json.dumps(record.to_dict(), default=str)
    print(log_line, file=sys.stdout, flush=True)
