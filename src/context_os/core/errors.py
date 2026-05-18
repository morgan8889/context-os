"""Structured error types for Context-OS.

All errors are serializable to dict for API error responses. The HTTP layer
maps subclass types to appropriate status codes.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ContextOSError(Exception):
    """Base error for all Context-OS errors.

    Attributes:
        code: Machine-readable error code for API responses.
        message: Human-readable description.
        trace_id: OTEL trace ID for log correlation (may be None outside span context).
    """

    code: str
    message: str
    trace_id: str | None = field(default=None)

    def to_dict(self) -> dict[str, str | int | None]:
        """Serialize to a dict suitable for JSON API error responses."""
        return {
            "code": self.code,
            "message": self.message,
            "trace_id": self.trace_id,
        }

    def __str__(self) -> str:
        return f"{self.code}: {self.message}"


@dataclass
class AuthError(ContextOSError):
    """Raised when JWT verification fails or the token is missing."""

    code: str = field(default="auth_error")
    message: str = field(default="Authentication failed")


@dataclass
class TenantIsolationError(ContextOSError):
    """Raised when a query is attempted without a valid tenant_id."""

    code: str = field(default="tenant_isolation_error")
    message: str = field(default="Tenant ID is required for this operation")


@dataclass
class TokenExpiredError(ContextOSError):
    """Raised when an OAuth access token has expired or been revoked."""

    code: str = field(default="token_expired")
    message: str = field(default="OAuth token has expired; please re-authenticate")


@dataclass
class RateLimitError(ContextOSError):
    """Raised when an upstream API returns 429 Too Many Requests.

    Attributes:
        retry_after: Number of seconds to wait before retrying.
    """

    retry_after: int = field(default=60)
    code: str = field(default="rate_limited")
    message: str = field(default="Rate limit reached; backing off")

    def to_dict(self) -> dict[str, str | int | None]:
        """Serialize to a dict, including retry_after."""
        base = super().to_dict()
        return {**base, "retry_after": self.retry_after}


@dataclass
class CheckpointError(ContextOSError):
    """Raised when checkpoint read/write fails."""

    code: str = field(default="checkpoint_error")
    message: str = field(default="Failed to read or write sync checkpoint")


@dataclass
class GraphQueryError(ContextOSError):
    """Raised when an AGE Cypher query fails."""

    code: str = field(default="graph_query_error")
    message: str = field(default="Graph query failed")


@dataclass
class VectorSearchError(ContextOSError):
    """Raised when a pgvector similarity search fails."""

    code: str = field(default="vector_search_error")
    message: str = field(default="Vector search failed")


@dataclass
class ValidationError(ContextOSError):
    """Raised when request input validation fails."""

    code: str = field(default="validation_error")
    message: str = field(default="Request validation failed")


# ── Phase 2: Intelligence error types ─────────────────────────────────────────


@dataclass
class AgentError(ContextOSError):
    """Raised when an AI agent (Synthesizer or Mapper) encounters a fatal error."""

    code: str = field(default="agent_error")
    message: str = field(default="Agent encountered a fatal error")


@dataclass
class ApprovalError(ContextOSError):
    """Raised when an approval action fails (e.g. item not found or wrong status).

    Attributes:
        item_id: UUID string of the ApprovalItem that caused the error.
    """

    item_id: str = field(default="")
    code: str = field(default="approval_error")
    message: str = field(default="Approval action failed")

    def to_dict(self) -> dict[str, str | int | None]:
        """Serialize to a dict, including item_id."""
        base = super().to_dict()
        return {**base, "item_id": self.item_id}


@dataclass
class EvalError(ContextOSError):
    """Raised when an evaluation suite run fails or a CI gate threshold is not met."""

    code: str = field(default="eval_error")
    message: str = field(default="Evaluation suite failed or CI gate not met")


@dataclass
class BudgetExceededError(AgentError):
    """Raised when an agent's token cost exceeds the configured budget.

    Attributes:
        tokens_used: Total tokens consumed before budget was exceeded.
        budget: The configured budget limit.
    """

    tokens_used: int = field(default=0)
    budget: int = field(default=50000)
    code: str = field(default="budget_exceeded")
    message: str = field(default="Agent token budget exceeded")

    def to_dict(self) -> dict[str, str | int | None]:
        """Serialize to a dict, including token counts."""
        base = super().to_dict()
        return {**base, "tokens_used": self.tokens_used, "budget": self.budget}


@dataclass
class WorkflowError(ContextOSError):
    """Raised when a LangGraph workflow fails to start, run, or resume.

    Attributes:
        thread_id: LangGraph thread ID (if applicable).
    """

    thread_id: str | None = field(default=None)
    code: str = field(default="workflow_error")
    message: str = field(default="Workflow failed")

    def to_dict(self) -> dict[str, str | int | None]:
        """Serialize to a dict, including thread_id."""
        base = super().to_dict()
        return {**base, "thread_id": self.thread_id}
