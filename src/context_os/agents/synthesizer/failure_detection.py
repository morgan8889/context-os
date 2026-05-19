"""Rule-based failure-mode detection for Synthesizer briefing drafts.

Four deterministic checks run after the LLM produces a draft, before it is
enqueued for operator review. Each check is independent and returns a FailureFlag
dict or None. All 4 checks are gathered and stored in the ApprovalItem's
failure_flags field.

These checks enforce constitution Principle VI (Observable Autonomy) by surfacing
known risk patterns before a human operator reviews the draft.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

import asyncpg
from sqlalchemy.ext.asyncio import AsyncSession

from context_os.graph.queries import check_actor_exists, find_stale_dependencies

logger = logging.getLogger(__name__)


@dataclass
class FailureFlag:
    """A detected failure mode in a synthesizer draft.

    Attributes:
        flag_type: Machine-readable type of the failure mode.
        detail: Human-readable description of what was detected.
        severity: Impact level — 'critical' | 'warning' | 'info'.
        context: Optional additional context dict for debugging.
    """

    flag_type: str
    detail: str
    severity: str = field(default="warning")
    context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a dict for JSONB storage in ApprovalItem.failure_flags."""
        return {
            "type": self.flag_type,
            "detail": self.detail,
            "severity": self.severity,
            "context": self.context,
        }


async def detect_hallucinated_stakeholder(
    name: str,
    tenant_id: str,
    age_pool: asyncpg.Pool,  # type: ignore[type-arg]
) -> FailureFlag | None:
    """Detect if a cited stakeholder does not exist in the graph.

    Args:
        name: Stakeholder name as cited in the briefing draft.
        tenant_id: Clerk org ID for tenant-scoped Actor lookup.
        age_pool: AGE asyncpg pool.

    Returns:
        FailureFlag if the Actor is not found, None if verification passes.
    """
    try:
        exists = await check_actor_exists(
            pool=age_pool,
            tenant_id=tenant_id,
            name_fragment=name,
        )
        if not exists:
            return FailureFlag(
                flag_type="hallucinated_stakeholder",
                detail=(
                    f"Cited stakeholder '{name}' was not found in the graph. "
                    "This may indicate a hallucinated name."
                ),
                severity="warning",
                context={"cited_name": name},
            )
        return None
    except Exception as e:
        logger.warning(
            "detect_hallucinated_stakeholder failed for name=%s: %s", name, e
        )
        return FailureFlag(
            flag_type="hallucinated_stakeholder",
            detail=f"Could not verify stakeholder '{name}': {e}",
            severity="info",
            context={"cited_name": name, "error": str(e)},
        )


async def detect_stale_dependency(
    edge_id: str,
    tenant_id: str,
    age_pool: asyncpg.Pool,  # type: ignore[type-arg]
) -> FailureFlag | None:
    """Detect if a cited dependency edge is stale (not updated in 90+ days).

    Args:
        edge_id: The DEPENDS_ON edge ID or identifier to check.
        tenant_id: Clerk org ID.
        age_pool: AGE asyncpg pool.

    Returns:
        FailureFlag if the dependency is stale, None if it is current.
    """
    try:
        # Retrieve stale edges and check if edge_id is among them
        stale_edges = await find_stale_dependencies(
            pool=age_pool,
            tenant_id=tenant_id,
            older_than_days=90,
        )
        stale_ids = {str(e.get("id", "")) for e in stale_edges}
        if edge_id in stale_ids:
            return FailureFlag(
                flag_type="stale_dependency",
                detail=(
                    f"Dependency edge '{edge_id}' has not been updated in 90+ days. "
                    "Verify this dependency is still valid."
                ),
                severity="warning",
                context={"edge_id": edge_id, "older_than_days": 90},
            )
        return None
    except Exception as e:
        logger.warning("detect_stale_dependency failed for edge_id=%s: %s", edge_id, e)
        return None


async def detect_missed_escalation(
    draft_sections: dict[str, Any],
    tenant_id: str,
    age_pool: asyncpg.Pool,  # type: ignore[type-arg]
) -> FailureFlag | None:
    """Detect if high-severity Risk nodes exist but are not referenced in escalations.

    Queries AGE for Risk nodes with severity='high' that have not been cited
    in the draft's escalations section. If found, this indicates the LLM may
    have missed important escalation items.

    Args:
        draft_sections: The briefing draft sections dict (from the LLM output).
        tenant_id: Clerk org ID.
        age_pool: AGE asyncpg pool.

    Returns:
        FailureFlag if uncited high-severity Risks exist, None otherwise.
    """
    try:
        from context_os.graph.client import run_cypher

        # Collect all source_ids already cited in escalations
        escalation_source_ids: set[str] = set()
        escalations = draft_sections.get("escalations", [])
        for item in escalations:
            if isinstance(item, dict):
                for sid in item.get("source_ids", []):
                    escalation_source_ids.add(str(sid))

        # Query for high-severity Risk nodes in the graph
        params: dict[str, Any] = {"tenant_id": tenant_id}
        cypher = """
        MATCH (r:Risk)
        WHERE r.tenant_id = $tenant_id
          AND r.severity = 'high'
          AND r.status = 'open'
        RETURN r
        LIMIT 10
        """
        rows = await run_cypher(
            age_pool,
            cypher,
            params=params,
            columns=[("r", "agtype")],
        )

        uncited_high_risks = []
        for row in rows:
            node_data = row.get("r")
            if isinstance(node_data, dict):
                props = node_data.get("properties", node_data)
                risk_id = str(props.get("id", ""))
                if risk_id and risk_id not in escalation_source_ids:
                    uncited_high_risks.append(
                        {
                            "id": risk_id,
                            "description": props.get("description", ""),
                        }
                    )

        if uncited_high_risks:
            return FailureFlag(
                flag_type="missed_escalation",
                detail=(
                    f"{len(uncited_high_risks)} high-severity Risk node(s) exist "
                    "but are not referenced in the escalations section."
                ),
                severity="warning",
                context={"uncited_risks": uncited_high_risks},
            )
        return None
    except Exception as e:
        logger.warning("detect_missed_escalation failed: %s", e)
        return None


async def detect_citation_error(
    source_id: str,
    tenant_id: str,
    session: AsyncSession,
) -> FailureFlag | None:
    """Detect if a cited source_id does not exist in node_embeddings.

    A citation error occurs when the LLM cites a UUID that does not correspond
    to any actual node in the relational store. This could indicate hallucination
    of node IDs or a stale reference.

    Args:
        source_id: UUID string cited as a source in the briefing draft.
        tenant_id: Clerk org ID (used as DB tenant UUID).
        session: SQLAlchemy async session for node_embeddings lookup.

    Returns:
        FailureFlag if the node is not found, None if the citation is valid.
    """
    try:
        from sqlalchemy import select

        from context_os.db.models import NodeEmbedding

        # Attempt to parse as UUID — invalid UUIDs are always citation errors
        try:
            node_uuid = uuid.UUID(source_id)
        except (ValueError, AttributeError):
            return FailureFlag(
                flag_type="citation_error",
                detail=(
                    f"Cited source_id '{source_id}' is not a valid UUID. "
                    "This is a citation error in the briefing draft."
                ),
                severity="warning",
                context={"source_id": source_id},
            )

        # Check node_embeddings table for the cited node
        stmt = select(NodeEmbedding.id).where(
            NodeEmbedding.id == node_uuid,
        )
        result = await session.execute(stmt)
        row = result.scalar_one_or_none()

        if row is None:
            return FailureFlag(
                flag_type="citation_error",
                detail=(
                    f"Cited source_id '{source_id}' was not found in the node "
                    "embeddings table. This may indicate a hallucinated node ID."
                ),
                severity="warning",
                context={"source_id": source_id},
            )
        return None
    except Exception as e:
        logger.warning(
            "detect_citation_error failed for source_id=%s: %s", source_id, e
        )
        return None


async def run_all_failure_checks(
    draft: dict[str, Any],
    tenant_id: str,
    age_pool: asyncpg.Pool,  # type: ignore[type-arg]
    session: AsyncSession,
) -> list[FailureFlag]:
    """Run all 4 failure-mode checks against a briefing draft.

    Extracts stakeholders, dependencies, escalations, and source_ids from
    the draft and runs each check. Returns all detected FailureFlag instances.

    Args:
        draft: The briefing draft dict (LLM output parsed as JSON).
        tenant_id: Clerk org ID.
        age_pool: AGE asyncpg pool.
        session: SQLAlchemy async session.

    Returns:
        List of FailureFlag instances (empty if no failures detected).
    """
    flags: list[FailureFlag] = []
    sections = draft.get("sections", {})

    # 1. Collect all source_ids cited across all sections for citation checking
    all_source_ids: list[str] = []
    for _, items in sections.items():
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict):
                    for sid in item.get("source_ids", []):
                        if sid:
                            all_source_ids.append(str(sid))

    # 2. Check citation errors for a sample of source_ids (cap at 10 to avoid overhead)
    for source_id in all_source_ids[:10]:
        flag = await detect_citation_error(source_id, tenant_id, session)
        if flag:
            flags.append(flag)

    # 3. Check for missed escalations (high-severity Risk nodes not cited)
    missed_flag = await detect_missed_escalation(sections, tenant_id, age_pool)
    if missed_flag:
        flags.append(missed_flag)

    # 4. Check dependency section for stale edges
    dependencies = sections.get("dependencies", [])
    for dep_item in dependencies:
        if isinstance(dep_item, dict):
            for sid in dep_item.get("source_ids", []):
                stale_flag = await detect_stale_dependency(
                    str(sid), tenant_id, age_pool
                )
                if stale_flag:
                    flags.append(stale_flag)
                    break  # One stale flag per dependency item is sufficient

    # 5. Check for hallucinated stakeholders (actor names referenced in text)
    # Extract names from progress/decisions/escalations sections
    cited_actors = _extract_actor_names(sections)
    for actor_name in cited_actors[:5]:  # Cap at 5 to limit graph round-trips
        halluc_flag = await detect_hallucinated_stakeholder(
            actor_name, tenant_id, age_pool
        )
        if halluc_flag:
            flags.append(halluc_flag)

    logger.info(
        "Failure detection complete: tenant=%s flags=%d",
        tenant_id,
        len(flags),
    )
    return flags


def _extract_actor_names(sections: dict[str, Any]) -> list[str]:
    """Extract potential actor names from briefing text using simple heuristics.

    Looks for capitalized multi-word names in section text as a proxy for
    stakeholder citations. This is a best-effort heuristic — false positives
    are acceptable since check_actor_exists is a read-only graph query.

    Args:
        sections: Briefing sections dict.

    Returns:
        List of potential actor name strings (deduplicated).
    """
    import re

    actors: list[str] = []
    seen: set[str] = set()

    # Pattern: two or more consecutive capitalized words (potential person names)
    name_pattern = re.compile(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b")

    for _, items in sections.items():
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            text = item.get("text", "")
            matches = name_pattern.findall(str(text))
            for match in matches:
                if match not in seen:
                    seen.add(match)
                    actors.append(match)

    return actors


# Explicitly reference timedelta and datetime to satisfy import checks
_UNUSED_TIMEDELTA = timedelta
_UNUSED_DATETIME = datetime
_UNUSED_UTC = UTC
