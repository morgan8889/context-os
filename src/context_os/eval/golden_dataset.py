"""Golden dataset management for eval suites.

Provides dataclasses and async functions for loading and building golden
datasets used by the Synthesizer and Dependency Mapper eval runners.
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, cast

from context_os.relational.repositories import (
    ApprovalItemRepository,
    GoldenDatasetRepository,
)

logger = logging.getLogger(__name__)


# ── Record dataclasses ────────────────────────────────────────────────────────


@dataclass
class GoldenRecord:
    """A single record in a golden dataset.

    For synthesizer datasets:
        - window_start, window_end: ISO 8601 timestamps for the briefing window.
        - draft_content: JSON dict of the draft as produced by the Synthesizer.
        - approved_content: JSON dict of the final approved content.
        - accepted_as_is: True if the draft was approved without edits.
        - edit_delta: Dict from difflib comparison (or None if accepted_as_is).
        - failure_mode_injections: List of dicts describing injected failure modes.

    For mapper datasets:
        - from_node_id: Source initiative UUID string.
        - to_node_id: Target initiative UUID string.
        - ground_truth_exists: True if this dependency actually exists.
        - evidence_signals: List of Signal node IDs cited as evidence.
    """

    # Synthesizer fields
    window_start: str | None = None
    window_end: str | None = None
    draft_content: dict[str, Any] = field(default_factory=dict)
    approved_content: dict[str, Any] = field(default_factory=dict)
    accepted_as_is: bool = False
    edit_delta: dict[str, Any] | None = None
    failure_mode_injections: list[dict[str, Any]] = field(default_factory=list)

    # Mapper fields
    from_node_id: str | None = None
    to_node_id: str | None = None
    ground_truth_exists: bool = False
    evidence_signals: list[str] = field(default_factory=list)


@dataclass
class GoldenDataset:
    """A named, versioned collection of golden records.

    Attributes:
        records: The individual evaluation records.
        version: Semver string (e.g. "1.0.0").
        dataset_type: "synthesizer" | "mapper".
        description: Human-readable description of the dataset.
        dataset_id: Optional UUID if loaded from the database.
    """

    records: list[GoldenRecord]
    version: str
    dataset_type: str
    description: str = ""
    dataset_id: str | None = None


# ── Loaders ───────────────────────────────────────────────────────────────────


async def load_dataset(
    eval_type: str,
    version: str,
    repo: GoldenDatasetRepository,
) -> GoldenDataset:
    """Load a golden dataset from the database by type and version.

    Args:
        eval_type: "synthesizer" | "mapper".
        version: Dataset version string (e.g. "1.0.0").
        repo: GoldenDatasetRepository for database access.

    Returns:
        GoldenDataset loaded from the database.

    Raises:
        ValueError: If no dataset of the given type/version exists.
    """
    db_dataset = await repo.get_latest_by_type(
        dataset_type=eval_type,
    )
    if db_dataset is None:
        raise ValueError(
            f"No golden dataset found for eval_type={eval_type!r} version={version!r}"
        )

    content = db_dataset.content or {}
    raw_records = cast(list[dict[str, Any]], content.get("records", []))
    records = [_deserialize_record(r, eval_type) for r in raw_records]

    return GoldenDataset(
        records=records,
        version=db_dataset.version or version,
        dataset_type=eval_type,
        description=db_dataset.description or "",
        dataset_id=str(db_dataset.id),
    )


def load_dataset_from_json(path: str, eval_type: str) -> GoldenDataset:
    """Load a golden dataset from a local JSON file.

    Used in tests where a real DB is not available.

    Args:
        path: Absolute path to the JSON file.
        eval_type: "synthesizer" | "mapper".

    Returns:
        GoldenDataset loaded from the file.
    """
    with open(path) as f:
        data = json.load(f)

    raw_records = data.get("records", [])
    records = [_deserialize_record(r, eval_type) for r in raw_records]

    return GoldenDataset(
        records=records,
        version=data.get("version", "1.0.0"),
        dataset_type=eval_type,
        description=data.get("description", ""),
    )


# ── Builders ─────────────────────────────────────────────────────────────────


async def build_synthesizer_dataset(
    tenant_id: str,
    approval_item_ids: list[str],
    injections: list[dict[str, Any]],
    approval_repo: ApprovalItemRepository,
    golden_repo: GoldenDatasetRepository,
    version: str = "1.0.0",
    description: str = "",
) -> GoldenDataset:
    """Build a synthesizer golden dataset from approved ApprovalItems.

    Fetches the specified ApprovalItems (must be briefing_draft type),
    extracts draft and approved content, and optionally appends synthetic
    failure-mode injection records.

    Args:
        tenant_id: Clerk org ID.
        approval_item_ids: List of ApprovalItem UUID strings to include.
        injections: List of failure-mode injection dicts to append as records.
        approval_repo: ApprovalItemRepository for fetching items.
        golden_repo: GoldenDatasetRepository for persisting the dataset.
        version: Semver version string for this dataset.
        description: Human-readable description.

    Returns:
        GoldenDataset persisted to the database.
    """
    records: list[GoldenRecord] = []

    for item_id_str in approval_item_ids:
        try:
            item_id = uuid.UUID(item_id_str)
        except ValueError:
            logger.warning("Invalid approval_item_id: %s", item_id_str)
            continue

        item = await approval_repo.get_by_id(item_id, tenant_id)
        if item is None:
            logger.warning("ApprovalItem not found: %s", item_id_str)
            continue

        if item.item_type != "briefing_draft":
            logger.warning(
                "Skipping non-briefing_draft item: %s (type=%s)",
                item_id_str,
                item.item_type,
            )
            continue

        # Extract draft and approved content from item content
        content: dict[str, Any] = cast(dict[str, Any], item.content or {})
        draft_content: dict[str, Any] = cast(
            dict[str, Any], content.get("sections", content)
        )
        approved_content: dict[str, Any] = cast(dict[str, Any], item.content or {})

        raw_edit_delta = item.edit_delta
        edit_delta: dict[str, Any] | None = (
            cast(dict[str, Any], raw_edit_delta) if raw_edit_delta else None
        )
        similarity = (
            float(edit_delta.get("similarity_ratio", 0.0)) if edit_delta else None
        )
        accepted_as_is = edit_delta is None or (
            similarity is not None and similarity >= 0.99
        )

        records.append(
            GoldenRecord(
                window_start=cast(str | None, content.get("window_start")),
                window_end=cast(str | None, content.get("window_end")),
                draft_content=draft_content,
                approved_content=approved_content,
                accepted_as_is=accepted_as_is,
                edit_delta=edit_delta,
                failure_mode_injections=[],
            )
        )

    # Append injection records for failure-mode testing
    for injection in injections:
        records.append(
            GoldenRecord(
                draft_content=injection.get("draft_content", {}),
                approved_content=injection.get("approved_content", {}),
                accepted_as_is=False,
                failure_mode_injections=[injection],
            )
        )

    # Serialize and persist
    serialized_records = [_serialize_record(r) for r in records]
    content_payload: dict[str, Any] = {
        "records": serialized_records,
        "version": version,
        "description": description,
        "built_at": datetime.now(UTC).isoformat(),
        "approval_item_ids": approval_item_ids,
    }

    db_dataset = await golden_repo.create(
        tenant_id=tenant_id,
        dataset_type="synthesizer",
        version=version,
        description=description,
        record_count=len(records),
        content=content_payload,
        built_from_approval_items=approval_item_ids,
    )

    logger.info(
        "build_synthesizer_dataset: tenant=%s records=%d version=%s dataset_id=%s",
        tenant_id,
        len(records),
        version,
        db_dataset.id,
    )

    return GoldenDataset(
        records=records,
        version=version,
        dataset_type="synthesizer",
        description=description,
        dataset_id=str(db_dataset.id),
    )


async def build_mapper_dataset(
    tenant_id: str,
    dependency_pairs: list[dict[str, Any]],
    golden_repo: GoldenDatasetRepository,
    version: str = "1.0.0",
    description: str = "",
) -> GoldenDataset:
    """Build a mapper golden dataset from held-out dependency pairs.

    Args:
        tenant_id: Clerk org ID.
        dependency_pairs: List of dicts with from_node_id, to_node_id,
            ground_truth_exists, evidence_signals.
        golden_repo: GoldenDatasetRepository for persisting the dataset.
        version: Semver version string for this dataset.
        description: Human-readable description.

    Returns:
        GoldenDataset persisted to the database.
    """
    records: list[GoldenRecord] = []

    for pair in dependency_pairs:
        records.append(
            GoldenRecord(
                from_node_id=pair.get("from_node_id", ""),
                to_node_id=pair.get("to_node_id", ""),
                ground_truth_exists=bool(pair.get("ground_truth_exists", False)),
                evidence_signals=pair.get("evidence_signals", []),
            )
        )

    serialized_records = [_serialize_record(r) for r in records]
    content_payload: dict[str, Any] = {
        "records": serialized_records,
        "version": version,
        "description": description,
        "built_at": datetime.now(UTC).isoformat(),
    }

    db_dataset = await golden_repo.create(
        tenant_id=tenant_id,
        dataset_type="mapper",
        version=version,
        description=description,
        record_count=len(records),
        content=content_payload,
        built_from_approval_items=[],
    )

    logger.info(
        "build_mapper_dataset: tenant=%s records=%d version=%s dataset_id=%s",
        tenant_id,
        len(records),
        version,
        db_dataset.id,
    )

    return GoldenDataset(
        records=records,
        version=version,
        dataset_type="mapper",
        description=description,
        dataset_id=str(db_dataset.id),
    )


# ── Serialization helpers ─────────────────────────────────────────────────────


def _serialize_record(record: GoldenRecord) -> dict[str, Any]:
    """Serialize a GoldenRecord to a JSON-compatible dict."""
    return {
        "window_start": record.window_start,
        "window_end": record.window_end,
        "draft_content": record.draft_content,
        "approved_content": record.approved_content,
        "accepted_as_is": record.accepted_as_is,
        "edit_delta": record.edit_delta,
        "failure_mode_injections": record.failure_mode_injections,
        "from_node_id": record.from_node_id,
        "to_node_id": record.to_node_id,
        "ground_truth_exists": record.ground_truth_exists,
        "evidence_signals": record.evidence_signals,
    }


def _deserialize_record(data: dict[str, Any], eval_type: str) -> GoldenRecord:
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
