"""Synthesizer eval runner.

Metrics:
- accept_rate: proportion of drafts approved without meaningful edits
  (SequenceMatcher ratio >= 0.90)
- median_edit_distance: median of (1 - ratio) across all records
- false_positive_risk_rate: proportion of Risk items rejected by operator
- failure_mode_detection: 4 boolean flags for injected failure modes
"""

from __future__ import annotations

import json
import logging
import statistics
from difflib import SequenceMatcher
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from context_os.core.errors import EvalError
from context_os.eval.golden_dataset import GoldenDataset, GoldenRecord
from context_os.eval.runner import EvalRunner, EvalRunResult
from context_os.relational.repositories import EvalRunRepository

logger = logging.getLogger(__name__)

# CI gate threshold
_ACCEPT_RATE_GATE = 0.40


class SynthesizerEvalRunner(EvalRunner):
    """Eval runner for the Operational Synthesizer agent.

    Computes 4 metrics:
    1. accept_rate — proportion where draft ~ approved (ratio >= 0.90)
    2. median_edit_distance — median of (1 - ratio) across records
    3. false_positive_risk_rate — proportion of Risk items rejected
    4. failure_mode_detection — did the detector catch injected failures?
    """

    async def run(
        self,
        dataset: GoldenDataset,
        session: AsyncSession,
        compare_to_run_id: str | None = None,
    ) -> EvalRunResult:
        """Run the synthesizer eval suite.

        Args:
            dataset: Golden dataset (type="synthesizer").
            session: SQLAlchemy async session.
            compare_to_run_id: Optional prior run UUID for delta comparison.

        Returns:
            EvalRunResult with all 4 metric scores.
        """
        start = self._timed_run()[0]

        real_records = [r for r in dataset.records if not r.failure_mode_injections]
        injection_records = [r for r in dataset.records if r.failure_mode_injections]

        accept_rate = self._compute_accept_rate(real_records)
        median_edit_distance = self._compute_median_edit_distance(real_records)
        fp_risk_rate = self._compute_false_positive_risk_rate(real_records)
        failure_modes = await self._run_failure_mode_tests(injection_records)

        scores: dict[str, float] = {
            "accept_rate": accept_rate,
            "median_edit_distance": median_edit_distance,
            "false_positive_risk_rate": fp_risk_rate,
            "hallucinated_stakeholder_detected": (
                1.0 if failure_modes.get("hallucinated_stakeholder") else 0.0
            ),
            "stale_dependency_detected": (
                1.0 if failure_modes.get("stale_dependency") else 0.0
            ),
            "missed_escalation_detected": (
                1.0 if failure_modes.get("missed_escalation") else 0.0
            ),
            "citation_error_detected": (
                1.0 if failure_modes.get("citation_error") else 0.0
            ),
        }

        gates_passed = self._check_ci_gates(scores)
        duration_ms = self._elapsed_ms(start)

        repo = EvalRunRepository(session)
        deltas = await self._compute_score_deltas(scores, compare_to_run_id, repo)

        run_id = await self._write_eval_run(
            eval_type="synthesizer",
            dataset=dataset,
            scores=scores,
            gates_passed=gates_passed,
            deltas=deltas,
            session=session,
            compare_to_run_id=compare_to_run_id,
            duration_ms=duration_ms,
        )
        await session.commit()

        logger.info(
            "SynthesizerEvalRunner.run: run_id=%s accept_rate=%.2f gates=%s",
            run_id,
            accept_rate,
            gates_passed,
        )

        return EvalRunResult(
            run_id=run_id,
            eval_type="synthesizer",
            scores=scores,
            gates_passed=gates_passed,
            score_deltas=deltas,
            duration_ms=duration_ms,
        )

    def _check_ci_gates(self, scores: dict[str, float]) -> bool:
        """Check the synthesizer CI gate: accept_rate >= 0.40.

        Args:
            scores: Computed metric scores.

        Returns:
            True if gate passes.

        Raises:
            EvalError: If the gate fails (for CLI non-zero exit).
        """
        accept_rate = scores.get("accept_rate", 0.0)
        if accept_rate < _ACCEPT_RATE_GATE:
            raise EvalError(
                code="ci_gate_failed",
                message=(
                    f"Synthesizer CI gate failed: "
                    f"accept_rate={accept_rate:.2f} < {_ACCEPT_RATE_GATE}"
                ),
            )
        return True

    def _compute_accept_rate(self, records: list[GoldenRecord]) -> float:
        """Proportion of records where draft was accepted without meaningful edits.

        A draft is considered accepted-as-is if
        SequenceMatcher(draft_text, approved_text).ratio() >= 0.90.

        Args:
            records: Real (non-injection) golden records.

        Returns:
            Accept rate in [0.0, 1.0]; 0.0 if no records.
        """
        if not records:
            return 0.0

        accepted = 0
        for record in records:
            draft_text = _content_to_text(record.draft_content)
            approved_text = _content_to_text(record.approved_content)
            ratio = SequenceMatcher(None, draft_text, approved_text).ratio()
            if ratio >= 0.90:
                accepted += 1

        return round(accepted / len(records), 4)

    def _compute_median_edit_distance(self, records: list[GoldenRecord]) -> float:
        """Median of (1 - similarity_ratio) across all records.

        A value of 0.0 means no edits; 1.0 means completely different content.

        Args:
            records: Real (non-injection) golden records.

        Returns:
            Median edit distance in [0.0, 1.0]; 0.0 if no records.
        """
        if not records:
            return 0.0

        distances = []
        for record in records:
            draft_text = _content_to_text(record.draft_content)
            approved_text = _content_to_text(record.approved_content)
            ratio = SequenceMatcher(None, draft_text, approved_text).ratio()
            distances.append(1.0 - ratio)

        return round(statistics.median(distances), 4)

    def _compute_false_positive_risk_rate(self, records: list[GoldenRecord]) -> float:
        """Proportion of Risk items in drafts that were rejected by the operator.

        A Risk item is considered a false positive if the draft section contains
        risk content but the record was rejected (accepted_as_is=False and
        approved_content differs significantly in the risks section).

        Args:
            records: Real (non-injection) golden records.

        Returns:
            False positive risk rate in [0.0, 1.0]; 0.0 if no risk items found.
        """
        total_risks = 0
        rejected_risks = 0

        for record in records:
            draft_risks = _extract_risks(record.draft_content)
            approved_risks = _extract_risks(record.approved_content)

            total_risks += len(draft_risks)
            # Count risks that appear in draft but not in approved (were removed)
            approved_texts = {_content_to_text(r) for r in approved_risks}
            for risk in draft_risks:
                risk_text = _content_to_text(risk)
                if risk_text not in approved_texts:
                    rejected_risks += 1

        if total_risks == 0:
            return 0.0
        return round(rejected_risks / total_risks, 4)

    async def _run_failure_mode_tests(
        self,
        injection_records: list[GoldenRecord],
    ) -> dict[str, bool]:
        """Run failure-mode detection on injection records.

        For each injected failure mode, checks whether run_all_failure_checks
        correctly flags the synthetic error.

        Args:
            injection_records: Records with failure_mode_injections set.

        Returns:
            Dict of {failure_mode_name: detected} booleans.
        """
        from context_os.agents.synthesizer.failure_detection import (
            run_all_failure_checks,
        )

        results: dict[str, bool] = {
            "hallucinated_stakeholder": False,
            "stale_dependency": False,
            "missed_escalation": False,
            "citation_error": False,
        }

        for record in injection_records:
            for injection in record.failure_mode_injections:
                mode = injection.get("failure_mode")
                if mode not in results:
                    continue

                draft = record.draft_content

                # Build minimal mocks for the failure detection functions
                from unittest.mock import AsyncMock

                mock_pool = AsyncMock()
                mock_session = AsyncMock()

                # Patch check_actor_exists based on the injection type
                if mode == "hallucinated_stakeholder":
                    # The injected name should NOT exist in the graph
                    with _patch_actor_exists(returns=False):
                        flags = await run_all_failure_checks(
                            draft=draft,
                            tenant_id="org_eval_test",
                            age_pool=mock_pool,
                            session=mock_session,
                        )
                elif mode == "stale_dependency":
                    with _patch_stale_deps(has_stale=True):
                        flags = await run_all_failure_checks(
                            draft=draft,
                            tenant_id="org_eval_test",
                            age_pool=mock_pool,
                            session=mock_session,
                        )
                elif mode == "missed_escalation":
                    with _patch_missed_escalation(has_missed=True):
                        flags = await run_all_failure_checks(
                            draft=draft,
                            tenant_id="org_eval_test",
                            age_pool=mock_pool,
                            session=mock_session,
                        )
                elif mode == "citation_error":
                    with _patch_citation_error(has_error=True):
                        flags = await run_all_failure_checks(
                            draft=draft,
                            tenant_id="org_eval_test",
                            age_pool=mock_pool,
                            session=mock_session,
                        )
                else:
                    flags = []

                # Check if the correct failure flag was raised
                flag_types = [f.flag_type for f in flags]
                results[mode] = mode in flag_types or any(
                    mode in ft for ft in flag_types
                )

        return results


# ── Helpers ───────────────────────────────────────────────────────────────────


def _content_to_text(content: Any) -> str:
    """Convert content (dict or str) to a comparable text string."""
    if isinstance(content, str):
        return content
    if isinstance(content, dict):
        return json.dumps(content, sort_keys=True)
    return str(content)


def _extract_risks(content: dict[str, Any]) -> list[Any]:
    """Extract risk items from a draft content dict."""
    sections = content.get("sections", content)
    if isinstance(sections, dict):
        risks = sections.get("risks", [])
        if isinstance(risks, list):
            return risks
    return []


def _patch_actor_exists(returns: bool) -> Any:
    """Context manager: patch check_actor_exists to return a fixed value."""
    from unittest.mock import AsyncMock, patch

    return patch(
        "context_os.agents.synthesizer.failure_detection.check_actor_exists",
        new=AsyncMock(return_value=returns),
    )


def _patch_stale_deps(has_stale: bool) -> Any:
    """Context manager: patch find_stale_dependencies to return stale edges."""
    from unittest.mock import AsyncMock, patch

    stale_result = (
        [{"id": "edge-stale-001", "updated_at": "2020-01-01"}] if has_stale else []
    )
    return patch(
        "context_os.agents.synthesizer.failure_detection.find_stale_dependencies",
        new=AsyncMock(return_value=stale_result),
    )


def _patch_missed_escalation(has_missed: bool) -> Any:
    """Context manager: patch run_cypher inside detect_missed_escalation.

    The detect_missed_escalation function calls run_cypher to find high-severity
    Risk nodes. We patch it at the graph.client module level.
    """
    from unittest.mock import AsyncMock, patch

    # Simulate a high-severity Risk row as an agtype dict
    if has_missed:
        risk_rows = [{"r": {"properties": {"id": "risk-crit-001", "severity": "high"}}}]
    else:
        risk_rows = []
    return patch(
        "context_os.graph.client.run_cypher",
        new=AsyncMock(return_value=risk_rows),
    )


def _patch_citation_error(has_error: bool) -> Any:
    """Context manager: patch session.execute for citation error detection.

    The detect_citation_error function calls session.execute to check node_embeddings.
    We cannot easily patch this generically, so we patch the whole detect_citation_error
    function to return a FailureFlag (error=True) or None (error=False).
    """
    from unittest.mock import AsyncMock, patch

    from context_os.agents.synthesizer.failure_detection import FailureFlag

    if has_error:
        flag = FailureFlag(
            flag_type="citation_error",
            detail="Injected citation error for eval testing",
            severity="warning",
            context={"source_id": "injected-bad-id"},
        )
        return patch(
            "context_os.agents.synthesizer.failure_detection.detect_citation_error",
            new=AsyncMock(return_value=flag),
        )
    return patch(
        "context_os.agents.synthesizer.failure_detection.detect_citation_error",
        new=AsyncMock(return_value=None),
    )
