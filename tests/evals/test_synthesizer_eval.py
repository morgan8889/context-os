"""Synthesizer eval tests.

Tests parametrized failure-mode injection and golden dataset metrics.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from context_os.agents.synthesizer.failure_detection import FailureFlag
from context_os.eval.synthesizer_eval import SynthesizerEvalRunner

# ── Failure-mode injection tests ──────────────────────────────────────────────


def _make_draft_with_stakeholder(name: str) -> dict[str, Any]:
    """Build a draft dict with a named stakeholder in the progress section.

    The name must be two separate capitalized words (e.g. "Alice Smith") to
    match the actor-name extraction regex in failure_detection.py.
    """
    return {
        "sections": {
            "progress": [
                {"text": f"{name} approved the deployment.", "source_ids": ["sig-x"]}
            ],
            "risks": [],
            "decisions": [],
            "dependencies": [],
            "escalations": [],
        }
    }


def _make_draft_with_dependency(edge_id: str) -> dict[str, Any]:
    """Build a draft dict with a stale dependency reference.

    The edge_id must appear in source_ids of a dependency item so that
    run_all_failure_checks passes it to detect_stale_dependency.
    """
    return {
        "sections": {
            "progress": [],
            "risks": [],
            "decisions": [],
            "dependencies": [
                {
                    "text": f"Dependency on edge {edge_id}",
                    "source_ids": [edge_id],
                }
            ],
            "escalations": [],
        }
    }


def _make_draft_missing_escalation() -> dict[str, Any]:
    """Build a draft dict with a high-severity risk but no escalation."""
    return {
        "sections": {
            "progress": [],
            "risks": [
                {
                    "text": "Critical outage risk",
                    "severity": "critical",
                    "source_ids": ["sig-y"],
                }
            ],
            "decisions": [],
            "dependencies": [],
            "escalations": [],
        }
    }


def _make_draft_with_bad_citation(source_id: str) -> dict[str, Any]:
    """Build a draft dict citing a non-existent source_id."""
    return {
        "sections": {
            "progress": [{"text": "Work done.", "source_ids": [source_id]}],
            "risks": [],
            "decisions": [],
            "dependencies": [],
            "escalations": [],
        }
    }


# Pre-built FailureFlag for citation_error injection test.
_CITATION_FLAG = FailureFlag(
    flag_type="citation_error",
    detail="Injected citation error for parametrize test",
    severity="warning",
    context={"source_id": "nonexistent-node-id"},
)


@pytest.mark.nightly_eval
@pytest.mark.parametrize(
    "failure_mode,draft_factory,patch_target,patch_return",
    [
        (
            "hallucinated_stakeholder",
            # Use simple two-word name ("Ghost Fake") so the actor-name
            # extraction regex ([A-Z][a-z]+ [A-Z][a-z]+) matches correctly.
            lambda: _make_draft_with_stakeholder("Ghost Fake"),
            "context_os.agents.synthesizer.failure_detection.check_actor_exists",
            False,
        ),
        (
            "stale_dependency",
            lambda: _make_draft_with_dependency("edge-stale-999"),
            "context_os.agents.synthesizer.failure_detection.find_stale_dependencies",
            [{"id": "edge-stale-999", "updated_at": "2019-01-01"}],
        ),
        (
            "missed_escalation",
            _make_draft_missing_escalation,
            # run_cypher is lazily imported inside detect_missed_escalation;
            # patch it at the source module level so the lazy import resolves
            # to the mock. Returns an agtype-formatted row with a high-severity
            # Risk node that is NOT cited in the (empty) escalations section.
            "context_os.graph.client.run_cypher",
            [{"r": {"properties": {"id": "risk-crit-001", "severity": "high"}}}],
        ),
        (
            "citation_error",
            lambda: _make_draft_with_bad_citation("nonexistent-node-id"),
            # Patch the whole detect_citation_error function to return a
            # pre-built FailureFlag — avoids mocking the SQLAlchemy session
            # execute path.
            "context_os.agents.synthesizer.failure_detection.detect_citation_error",
            _CITATION_FLAG,
        ),
    ],
)
@pytest.mark.anyio
async def test_failure_mode_injection(
    failure_mode: str,
    draft_factory: Any,
    patch_target: str,
    patch_return: Any,
) -> None:
    """Each injected failure mode triggers the correct FailureFlag.

    Parametrized over all 4 failure modes. Patches the relevant graph/DB
    call to simulate the error condition and asserts that run_all_failure_checks
    returns a flag with the expected flag_type.
    """
    from context_os.agents.synthesizer.failure_detection import run_all_failure_checks

    draft = draft_factory()
    mock_pool = AsyncMock()
    mock_session = AsyncMock()

    with patch(patch_target, new=AsyncMock(return_value=patch_return)):
        flags = await run_all_failure_checks(
            draft=draft,
            tenant_id="org_eval_test",
            age_pool=mock_pool,
            session=mock_session,
        )

    flag_types = [f.flag_type for f in flags]
    assert any(failure_mode in ft for ft in flag_types), (
        f"Expected failure_mode={failure_mode!r} in flags, got: {flag_types}"
    )


# ── Golden dataset metrics tests ──────────────────────────────────────────────


@pytest.mark.nightly_eval
@pytest.mark.anyio
async def test_synthesizer_metrics_on_golden_dataset(
    load_golden_dataset: Any,
    mock_db_session: Any,
) -> None:
    """SynthesizerEvalRunner produces valid metric scores on the 5-record golden
    dataset.

    Asserts:
    - scores dict has all expected keys
    - accept_rate and median_edit_distance are floats in [0, 1]
    - run_id is a non-empty string
    """
    dataset = load_golden_dataset("synthesizer")
    assert len(dataset.records) == 5, f"Expected 5 records, got {len(dataset.records)}"

    runner = SynthesizerEvalRunner(tenant_id="org_eval_test")

    # Patch the EvalRunRepository.create and EvalRunRepository.update_scores
    # to avoid real DB interaction
    mock_run = MagicMock()
    mock_run.id = __import__("uuid").uuid4()

    # Pre-built FailureFlag for citation_error during golden dataset run
    citation_flag = FailureFlag(
        flag_type="citation_error",
        detail="Injected citation error for golden dataset test",
        severity="warning",
        context={"source_id": "injected-bad-id"},
    )

    with (
        patch(
            "context_os.eval.runner.EvalRunRepository",
            return_value=MagicMock(
                create=AsyncMock(return_value=mock_run),
                get_by_id=AsyncMock(return_value=None),
            ),
        ),
        patch(
            "context_os.agents.synthesizer.failure_detection.check_actor_exists",
            new=AsyncMock(return_value=False),
        ),
        patch(
            "context_os.agents.synthesizer.failure_detection.find_stale_dependencies",
            new=AsyncMock(return_value=[{"id": "edge-stale-001"}]),
        ),
        # missed_escalation: patch run_cypher at source so lazy import resolves
        # to the mock; return empty list so no uncited risks are found
        patch(
            "context_os.graph.client.run_cypher",
            new=AsyncMock(return_value=[]),
        ),
        # citation_error: patch detect_citation_error directly
        patch(
            "context_os.agents.synthesizer.failure_detection.detect_citation_error",
            new=AsyncMock(return_value=citation_flag),
        ),
    ):
        result = await runner.run(dataset=dataset, session=mock_db_session)

    # Verify score keys are present
    expected_keys = {
        "accept_rate",
        "median_edit_distance",
        "false_positive_risk_rate",
        "hallucinated_stakeholder_detected",
        "stale_dependency_detected",
        "missed_escalation_detected",
        "citation_error_detected",
    }
    assert expected_keys.issubset(set(result.scores.keys())), (
        f"Missing keys: {expected_keys - set(result.scores.keys())}"
    )

    # Validate metric ranges
    assert 0.0 <= result.scores["accept_rate"] <= 1.0, (
        f"accept_rate out of range: {result.scores['accept_rate']}"
    )
    assert 0.0 <= result.scores["median_edit_distance"] <= 1.0, (
        f"median_edit_distance out of range: {result.scores['median_edit_distance']}"
    )

    assert isinstance(result.run_id, str) and len(result.run_id) > 0
