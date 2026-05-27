"""Unit tests for DebugTraceService.

Langfuse API calls are mocked — no real Langfuse connection required.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _make_trace(operation_id: str = "op-123") -> dict:
    """Build a minimal mock Langfuse trace response."""
    return {
        "id": operation_id,
        "name": "synthesizer_run",
        "timestamp": "2026-05-21T10:00:00Z",
        "observations": [
            {
                "id": "span-1",
                "name": "llm_call",
                "startTime": "2026-05-21T10:00:01Z",
                "endTime": "2026-05-21T10:00:05Z",
                "input": {"messages": [{"role": "user", "content": "Summarise X"}]},
                "output": {"text": "Here is a summary of X..."},
                "type": "GENERATION",
            },
            {
                "id": "span-2",
                "name": "tool_call",
                "startTime": "2026-05-21T10:00:06Z",
                "endTime": "2026-05-21T10:00:07Z",
                "input": {"query": "fetch graph"},
                "output": {"nodes": 5},
                "type": "SPAN",
            },
        ],
    }


class TestDebugTraceServiceGetTrace:
    async def test_get_trace_returns_spans_ordered_by_start(self) -> None:
        """get_trace returns spans ordered by startTime ascending."""
        from context_os.api.support import DebugTraceService

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = _make_trace("op-abc")
        mock_resp.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=mock_resp)):
            with patch("context_os.api.support.get_settings") as mock_settings:
                settings = MagicMock()
                settings.langfuse_public_key = "pk-lf"
                settings.langfuse_secret_key = "sk-lf"
                settings.langfuse_host = "http://localhost:3000"
                mock_settings.return_value = settings

                svc = DebugTraceService()
                trace = await svc.get_trace("op-abc")

        assert trace.operation_id == "op-abc"
        assert len(trace.spans) == 2
        # Spans should be ordered by startTime
        start_times = [s.started_at for s in trace.spans]
        assert start_times == sorted(start_times)

    async def test_get_trace_raises_not_found_for_unknown_id(self) -> None:
        """get_trace raises NotFound when the operation_id does not exist."""
        from context_os.api.support import DebugTraceService, NotFound

        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_resp.raise_for_status.side_effect = Exception("404")

        with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=mock_resp)):
            with patch("context_os.api.support.get_settings") as mock_settings:
                settings = MagicMock()
                settings.langfuse_public_key = "pk-lf"
                settings.langfuse_secret_key = "sk-lf"
                settings.langfuse_host = "http://localhost:3000"
                mock_settings.return_value = settings

                svc = DebugTraceService()
                with pytest.raises(NotFound):
                    await svc.get_trace("unknown-op")


class TestRedactTrace:
    def test_redact_replaces_llm_content_with_token_count(self) -> None:
        """redact_trace replaces LLM text with token count summary."""
        from context_os.api.support import DebugTrace, DebugTraceSpan, redact_trace

        span1 = DebugTraceSpan(
            span_id="s1",
            name="llm_call",
            started_at="2026-05-21T10:00:01Z",
            ended_at="2026-05-21T10:00:05Z",
            span_type="GENERATION",
            input={"messages": [{"role": "user", "content": "A" * 100}]},
            output={"text": "B" * 200},
        )
        span2 = DebugTraceSpan(
            span_id="s2",
            name="tool_call",
            started_at="2026-05-21T10:00:06Z",
            ended_at="2026-05-21T10:00:07Z",
            span_type="SPAN",
            input={"query": "fetch graph"},
            output={"nodes": 5},
        )
        trace = DebugTrace(
            operation_id="op-xyz",
            name="test_run",
            timestamp="2026-05-21T10:00:00Z",
            spans=[span1, span2],
        )

        redacted = redact_trace(trace)

        # GENERATION span should have redacted input/output
        gen_span = next(s for s in redacted.spans if s.span_type == "GENERATION")
        assert "[REDACTED" in str(gen_span.input) or "[REDACTED" in str(gen_span.output)

        # SPAN (non-LLM) should be preserved
        tool_span = next(s for s in redacted.spans if s.span_type == "SPAN")
        assert tool_span.input == {"query": "fetch graph"}
