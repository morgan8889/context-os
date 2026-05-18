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
