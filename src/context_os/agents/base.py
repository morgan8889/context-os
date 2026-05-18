"""Abstract base class for Context-OS agents.

All agents must inherit from AbstractAgent, which provides:
- Required OTEL span emission with all 7 context_os.* attributes
- Abstract run() method contract
- Autonomy level enforcement per constitution Principle III
"""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from typing import Any

from opentelemetry import trace

from context_os.observability.tracer import get_tracer

logger = logging.getLogger(__name__)


class AbstractAgent(ABC):
    """Base class for all Context-OS AI agents.

    Every agent declares an identity and autonomy level, and wraps its
    primary action in an OTEL span carrying all required governance attributes.

    Attributes:
        agent_identity: Unique string identifier (e.g. 'synthesizer', 'mapper').
        autonomy_level: Integer 0–5 per constitution autonomy scale.
            Levels ≤3 must be reversible/auditable/gated.
            Levels 4–5 must publish escalation criteria.
    """

    agent_identity: str
    autonomy_level: int

    def __init__(self, tenant_id: str) -> None:
        """Initialize the agent with a tenant scope.

        Args:
            tenant_id: Clerk org ID — all agent operations are tenant-scoped.
        """
        self._tenant_id = tenant_id
        self._tracer: trace.Tracer | None = None

    def _get_tracer(self) -> trace.Tracer | None:
        """Return a lazy-initialized tracer for this agent.

        Returns:
            Tracer instance or None if tracer is not initialized (e.g. in tests).
        """
        if self._tracer is None:
            try:
                self._tracer = get_tracer(f"context_os.agents.{self.agent_identity}")
            except RuntimeError:
                pass  # Tracer not initialized (test context)
        return self._tracer

    async def _emit_agent_span(
        self,
        input_summary: str,
        output_summary: str,
        cost_tokens: int = 0,
        governance_markers: list[str] | None = None,
    ) -> None:
        """Emit an OTEL span with all required context_os.* attributes.

        Writes the 7 mandatory span attributes defined in the telemetry schema:
            context_os.agent_identity
            context_os.autonomy_level
            context_os.tenant_id
            context_os.input_summary
            context_os.output_summary
            context_os.governance_markers
            context_os.cost_tokens

        Args:
            input_summary: Human-readable description of agent inputs.
            output_summary: Human-readable description of agent outputs.
            cost_tokens: Total token cost (prompt + completion) for this run.
            governance_markers: List of governance tags (e.g. ["requires_approval"]).
        """
        tracer = self._get_tracer()
        if tracer is None:
            return

        markers = governance_markers or []
        span_name = f"context_os.agent.{self.agent_identity}"

        with tracer.start_as_current_span(span_name) as span:
            span.set_attribute("context_os.agent_identity", self.agent_identity)
            span.set_attribute("context_os.autonomy_level", self.autonomy_level)
            span.set_attribute("context_os.tenant_id", self._tenant_id)
            span.set_attribute("context_os.input_summary", input_summary)
            span.set_attribute("context_os.output_summary", output_summary)
            span.set_attribute("context_os.governance_markers", json.dumps(markers))
            span.set_attribute("context_os.cost_tokens", cost_tokens)

    def _emit_agent_span_sync(
        self,
        input_summary: str,
        output_summary: str,
        cost_tokens: int = 0,
        governance_markers: list[str] | None = None,
    ) -> trace.Span | None:
        """Start and return an OTEL span with all required context_os.* attributes.

        Unlike _emit_agent_span, this method starts the span and returns it for
        use as a context manager. Callers must exit the span explicitly.

        Args:
            input_summary: Human-readable description of agent inputs.
            output_summary: Human-readable description of agent outputs (initial).
            cost_tokens: Initial token cost estimate.
            governance_markers: List of governance tags.

        Returns:
            OTEL Span or None if tracer is unavailable.
        """
        tracer = self._get_tracer()
        if tracer is None:
            return None

        markers = governance_markers or []
        span_name = f"context_os.agent.{self.agent_identity}"
        span = tracer.start_span(span_name)

        span.set_attribute("context_os.agent_identity", self.agent_identity)
        span.set_attribute("context_os.autonomy_level", self.autonomy_level)
        span.set_attribute("context_os.tenant_id", self._tenant_id)
        span.set_attribute("context_os.input_summary", input_summary)
        span.set_attribute("context_os.output_summary", output_summary)
        span.set_attribute("context_os.governance_markers", json.dumps(markers))
        span.set_attribute("context_os.cost_tokens", cost_tokens)

        return span

    @abstractmethod
    async def run(self, **kwargs: Any) -> Any:
        """Execute the agent's primary action.

        All subclasses must override this method. Implementations should:
        1. Call _emit_agent_span() before or during execution.
        2. Return a structured result appropriate for the agent type.
        3. Never write to the canonical graph directly — all outputs go to
           ApprovalItem rows for operator review (autonomy_level ≤ 3 constraint).

        Args:
            **kwargs: Agent-specific input parameters.

        Returns:
            Agent-specific result object.
        """
        ...
