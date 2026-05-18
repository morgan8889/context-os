"""Abstract EvalRunner base and EvalRunResult dataclass.

Provides the common infrastructure for running eval suites:
- Score delta computation against prior runs
- EvalRun persistence
- CI gate enforcement
"""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from context_os.eval.golden_dataset import GoldenDataset
from context_os.relational.repositories import EvalRunRepository

logger = logging.getLogger(__name__)


# ── Result dataclass ──────────────────────────────────────────────────────────


@dataclass
class EvalRunResult:
    """Result of a complete eval run.

    Attributes:
        run_id: UUID string of the persisted EvalRun record.
        eval_type: "synthesizer" | "mapper".
        scores: Dict of metric_name -> float.
        gates_passed: True if all CI gates were satisfied.
        score_deltas: Dict of metric_name -> delta vs prior run (or None).
        duration_ms: Total eval duration in milliseconds.
    """

    run_id: str
    eval_type: str
    scores: dict[str, float]
    gates_passed: bool
    score_deltas: dict[str, float | None] = field(default_factory=dict)
    duration_ms: int = 0


# ── Abstract base ─────────────────────────────────────────────────────────────


class EvalRunner(ABC):
    """Abstract base class for evaluation runners.

    Subclasses implement:
    - `run()`: orchestrate metric computation and return EvalRunResult
    - `_check_ci_gates()`: raise EvalError if any CI gate fails

    The base provides:
    - `_compute_score_deltas()`: compare current scores vs prior EvalRun
    - `_write_eval_run()`: persist EvalRun record to the database
    """

    def __init__(self, tenant_id: str) -> None:
        """Initialize the runner with the active tenant.

        Args:
            tenant_id: Clerk org ID — used for all relational queries.
        """
        self._tenant_id = tenant_id

    @abstractmethod
    async def run(
        self,
        dataset: GoldenDataset,
        session: AsyncSession,
        compare_to_run_id: str | None = None,
    ) -> EvalRunResult:
        """Run the eval suite against the given dataset.

        Args:
            dataset: Golden dataset to evaluate against.
            session: SQLAlchemy async session for DB access.
            compare_to_run_id: Optional prior EvalRun UUID to compare scores against.

        Returns:
            EvalRunResult with scores, gates_passed, and score_deltas.
        """

    @abstractmethod
    def _check_ci_gates(self, scores: dict[str, float]) -> bool:
        """Check whether all CI gate thresholds are satisfied.

        Args:
            scores: Dict of metric_name -> float.

        Returns:
            True if all gates pass.

        Raises:
            EvalError: If any gate fails (for CLI usage that should exit non-zero).
        """

    async def _compute_score_deltas(
        self,
        current_scores: dict[str, float],
        prior_run_id: str | None,
        repo: EvalRunRepository,
    ) -> dict[str, float | None]:
        """Compute score deltas vs a prior EvalRun.

        Args:
            current_scores: Current run metric scores.
            prior_run_id: UUID string of the prior EvalRun (or None).
            repo: EvalRunRepository for fetching the prior run.

        Returns:
            Dict of metric_name -> delta (current - prior), or None if no prior.
        """
        if prior_run_id is None:
            return {k: None for k in current_scores}

        try:
            import uuid as _uuid

            prior_run = await repo.get_by_id(_uuid.UUID(prior_run_id), self._tenant_id)
        except Exception as exc:
            logger.warning("Failed to load prior EvalRun %s: %s", prior_run_id, exc)
            return {k: None for k in current_scores}

        if prior_run is None:
            return {k: None for k in current_scores}

        prior_scores: dict[str, Any] = prior_run.scores or {}
        deltas: dict[str, float | None] = {}
        for metric, value in current_scores.items():
            prior_value = prior_scores.get(metric)
            if prior_value is not None:
                deltas[metric] = round(float(value) - float(prior_value), 4)
            else:
                deltas[metric] = None
        return deltas

    async def _write_eval_run(
        self,
        eval_type: str,
        dataset: GoldenDataset,
        scores: dict[str, float],
        gates_passed: bool,
        deltas: dict[str, float | None],
        session: AsyncSession,
        compare_to_run_id: str | None,
        duration_ms: int,
    ) -> str:
        """Persist an EvalRun record and return its run_id string.

        Args:
            eval_type: "synthesizer" | "mapper".
            dataset: Golden dataset that was evaluated.
            scores: Computed metric scores.
            gates_passed: Whether all CI gates passed.
            deltas: Score deltas vs prior run.
            session: SQLAlchemy async session.
            compare_to_run_id: Prior run UUID string (or None).
            duration_ms: Total eval duration.

        Returns:
            UUID string of the created EvalRun record.
        """
        import uuid as _uuid

        repo = EvalRunRepository(session)

        # Convert deltas — store as float only (drop None values for JSON)
        serializable_deltas: dict[str, float] = {
            k: v for k, v in deltas.items() if v is not None
        }

        run = await repo.create(
            tenant_id=self._tenant_id,
            eval_type=eval_type,
            dataset_id=_uuid.UUID(dataset.dataset_id) if dataset.dataset_id else None,
            dataset_version=dataset.version,
            status="complete",
            scores=scores,
            gates_passed=gates_passed,
            compared_to_run_id=(
                _uuid.UUID(compare_to_run_id) if compare_to_run_id else None
            ),
            score_deltas=serializable_deltas,
            duration_ms=duration_ms,
        )

        run_id = str(run.id)
        logger.info(
            "_write_eval_run: eval_type=%s run_id=%s gates_passed=%s",
            eval_type,
            run_id,
            gates_passed,
        )
        return run_id

    def _timed_run(self) -> tuple[float, Any]:
        """Return the current monotonic time for duration measurement.

        Usage:
            start = self._timed_run()[0]
            ...
            elapsed_ms = int((time.monotonic() - start) * 1000)

        Returns:
            Tuple of (start_time, None) — the None is for destructuring convenience.
        """
        return time.monotonic(), None

    def _elapsed_ms(self, start: float) -> int:
        """Compute elapsed milliseconds since start.

        Args:
            start: Monotonic start time from _timed_run.

        Returns:
            Elapsed milliseconds as int.
        """
        return int((time.monotonic() - start) * 1000)
