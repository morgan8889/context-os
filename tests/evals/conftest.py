"""Pytest fixtures for the eval test suite.

Provides:
- load_golden_dataset: fixture that reads JSON files from tests/evals/golden/
- assert_ci_gate: session-scoped accumulator that fails if any metric is below threshold
- synthesizer_agent_fixture: mock SynthesizerAgent for unit-level eval tests
- ci_gpu_available: fixture reporting GPU availability from CI_GPU_AVAILABLE env var
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from context_os.eval.golden_dataset import GoldenDataset, GoldenRecord

_GOLDEN_DIR = Path(__file__).parent / "golden"

# Session-scoped accumulator for CI gate failures
_gate_failures: list[str] = []


# ── Dataset fixtures ──────────────────────────────────────────────────────────


@pytest.fixture
def load_golden_dataset():
    """Fixture: load a golden dataset from a JSON file in tests/evals/golden/.

    Usage:
        def test_foo(load_golden_dataset):
            dataset = load_golden_dataset("synthesizer")
            ...
    """

    def _load(eval_type: str) -> GoldenDataset:
        path = _GOLDEN_DIR / f"{eval_type}_v1.json"
        if not path.exists():
            raise FileNotFoundError(
                f"Golden dataset not found: {path}. "
                "Ensure tests/evals/golden/{eval_type}_v1.json exists."
            )
        with open(path) as f:
            data = json.load(f)

        raw_records = data.get("records", [])
        records = [_deserialize_record(r) for r in raw_records]

        return GoldenDataset(
            records=records,
            version=data.get("version", "1.0.0"),
            dataset_type=eval_type,
            description=data.get("description", ""),
        )

    return _load


def _deserialize_record(data: dict[str, Any]) -> GoldenRecord:
    """Deserialize a dict to a GoldenRecord."""
    return GoldenRecord(
        window_start=data.get("window_start"),
        window_end=data.get("window_end"),
        draft_content=data.get("draft_content") or {},
        approved_content=data.get("approved_content") or {},
        accepted_as_is=bool(data.get("accepted_as_is", False)),
        edit_delta=data.get("edit_delta"),
        failure_mode_injections=data.get("failure_mode_injections") or [],
        from_node_id=data.get("from_node_id"),
        to_node_id=data.get("to_node_id"),
        ground_truth_exists=bool(data.get("ground_truth_exists", False)),
        evidence_signals=data.get("evidence_signals") or [],
    )


# ── CI gate accumulator ───────────────────────────────────────────────────────


@pytest.fixture(scope="session", autouse=True)
def _clear_gate_failures():
    """Clear gate failures at the start of each session."""
    _gate_failures.clear()
    yield
    # Report any accumulated failures after the session
    if _gate_failures:
        failure_summary = "\n".join(f"  - {f}" for f in _gate_failures)
        pytest.fail(
            f"CI gate failures accumulated during session:\n{failure_summary}",
            pytrace=False,
        )


@pytest.fixture
def assert_ci_gate():
    """Session-scoped CI gate accumulator.

    Usage:
        def test_foo(assert_ci_gate):
            assert_ci_gate("accept_rate", 0.75, threshold=0.40)
    """

    def _assert(metric_name: str, value: float, threshold: float) -> None:
        if value < threshold:
            failure = f"{metric_name}={value:.4f} below threshold={threshold:.4f}"
            _gate_failures.append(failure)
            pytest.fail(
                f"CI gate failed: {failure}",
                pytrace=False,
            )

    return _assert


# ── GPU availability fixture ──────────────────────────────────────────────────


@pytest.fixture
def ci_gpu_available() -> bool:
    """Return True if CI_GPU_AVAILABLE env var is set to a non-empty value.

    Eval tests that require GPU-accelerated rendering (e.g. visual regression
    via Playwright) should skip when this fixture returns False in CI.

    Usage:
        def test_gpu_dependent(ci_gpu_available):
            if not ci_gpu_available:
                pytest.skip(reason="infrastructure-unavailable")
    """
    return bool(os.environ.get("CI_GPU_AVAILABLE"))


# ── Mock agent fixtures ───────────────────────────────────────────────────────


@pytest.fixture
def synthesizer_agent_fixture():
    """Return a mock SynthesizerAgent for unit-level eval tests.

    The mock returns a pre-configured BriefingState with 5 sections
    and no failure flags by default.
    """
    mock_state = {
        "tenant_id": "org_eval_test",
        "signals_retrieved": [
            {"id": f"sig-{i}", "source": "github", "content": f"Signal {i}"}
            for i in range(10)
        ],
        "draft_sections": {
            "sections": {
                "progress": [{"text": "Sprint complete", "source_ids": ["sig-0"]}],
                "risks": [
                    {
                        "text": "Auth service slow",
                        "severity": "medium",
                        "source_ids": ["sig-1"],
                    }
                ],
                "decisions": [{"text": "Use ruff", "source_ids": ["sig-2"]}],
                "dependencies": [{"text": "Blocked on infra", "source_ids": ["sig-3"]}],
                "escalations": [{"text": "None", "source_ids": []}],
            }
        },
        "failure_flags": [],
        "cost_tokens": 1500,
        "approval_item_id": "item-mock-001",
        "error": None,
    }

    agent = MagicMock()
    agent.run = AsyncMock(return_value=mock_state)
    agent.agent_identity = "synthesizer"
    agent.autonomy_level = 2
    return agent
