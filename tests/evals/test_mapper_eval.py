"""Mapper eval tests.

Tests metrics on the 10-record golden dataset and CI gate enforcement.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from context_os.core.errors import EvalError
from context_os.eval.golden_dataset import GoldenDataset, GoldenRecord
from context_os.eval.mapper_eval import MapperEvalRunner


def _mock_run() -> MagicMock:
    """Return a mock EvalRun ORM object."""
    run = MagicMock()
    run.id = __import__("uuid").uuid4()
    return run


@pytest.mark.nightly_eval
@pytest.mark.anyio
async def test_mapper_metrics_on_golden_dataset(
    load_golden_dataset: Any,
    mock_db_session: Any,
) -> None:
    """MapperEvalRunner produces valid precision/recall/fp_rate on the 10-record
    dataset.

    The golden dataset has 7 ground-truth-exists=True and 3 false positives.

    Asserts:
    - precision, recall, false_positive_rate are floats in [0, 1]
    - precision + false_positive_rate ≈ 1.0 (they partition proposed edges)
    - run_id is a non-empty string
    """
    dataset = load_golden_dataset("mapper")
    assert len(dataset.records) == 10, (
        f"Expected 10 records, got {len(dataset.records)}"
    )

    runner = MapperEvalRunner(tenant_id="org_eval_test")

    with patch(
        "context_os.eval.runner.EvalRunRepository",
        return_value=MagicMock(
            create=AsyncMock(return_value=_mock_run()),
            get_by_id=AsyncMock(return_value=None),
        ),
    ):
        result = await runner.run(dataset=dataset, session=mock_db_session)

    precision = result.scores["precision"]
    recall = result.scores["recall"]
    fp_rate = result.scores["false_positive_rate"]

    assert 0.0 <= precision <= 1.0, f"precision out of range: {precision}"
    assert 0.0 <= recall <= 1.0, f"recall out of range: {recall}"
    assert 0.0 <= fp_rate <= 1.0, f"false_positive_rate out of range: {fp_rate}"

    # For a 10-record dataset: 7 true / 3 false
    # precision = 7/10 = 0.7, fp_rate = 3/10 = 0.3
    # precision + fp_rate should = 1.0 (they partition all records)
    assert abs(precision + fp_rate - 1.0) < 0.01, (
        f"precision ({precision}) + fp_rate ({fp_rate}) should sum to ~1.0"
    )

    # Recall = proposed_true / ground_truth_count = 7/7 = 1.0
    # (all ground-truth records are included in the dataset)
    assert recall == 1.0, f"Expected recall=1.0 for this dataset, got {recall}"

    assert isinstance(result.run_id, str) and len(result.run_id) > 0


@pytest.mark.nightly_eval
@pytest.mark.anyio
async def test_ci_gate_fails_on_low_recall(mock_db_session: Any) -> None:
    """MapperEvalRunner raises EvalError when recall < 0.50.

    Creates a dataset where all records have ground_truth_exists=False
    (recall=0.0), runs MapperEvalRunner, and asserts EvalError is raised.
    """
    # All records are false positives — no ground truth exists
    records = [
        GoldenRecord(
            from_node_id=f"initiative-{i:03d}",
            to_node_id=f"initiative-{i + 1:03d}",
            ground_truth_exists=False,
            evidence_signals=[],
        )
        for i in range(5)
    ]

    dataset = GoldenDataset(
        records=records,
        version="1.0.0",
        dataset_type="mapper",
        description="All-false-positive dataset for CI gate test",
    )

    runner = MapperEvalRunner(tenant_id="org_eval_test")

    with pytest.raises(EvalError) as exc_info:
        await runner.run(dataset=dataset, session=mock_db_session)

    assert "recall" in exc_info.value.message.lower(), (
        f"Expected 'recall' in error message, got: {exc_info.value.message}"
    )
    assert "0.50" in exc_info.value.message or "0.5" in exc_info.value.message, (
        f"Expected threshold in error message, got: {exc_info.value.message}"
    )
