"""Ingest API endpoints.

POST /ingest/{integration} — trigger incremental ingest
GET /ingest/{integration}/status — get last checkpoint status

All routes require Clerk JWT authentication via get_current_tenant dependency.
"""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from context_os.auth.dependencies import TenantContext, get_current_tenant
from context_os.core.errors import TokenExpiredError
from context_os.db.engine import get_session_factory
from context_os.graph.client import get_age_pool
from context_os.graph.mutations import upsert_node
from context_os.observability.schema import (
    EVENT,
    StructuredLogRecord,
    emit_structured_log,
)
from context_os.observability.tracer import get_current_trace_id, get_tracer
from context_os.relational.repositories import (
    CheckpointRepository,
    OAuthTokenRepository,
)
from context_os.vector.embeddings import get_embedding_model

logger = logging.getLogger(__name__)
router = APIRouter()
_tracer = None


def _get_tracer() -> Any:
    global _tracer
    if _tracer is None:
        try:
            _tracer = get_tracer("context_os.api.ingest")
        except RuntimeError:
            pass
    return _tracer


class IngestStatusResponse(BaseModel):
    """Response schema for ingest status."""

    status: str
    integration: str
    tenant_id: str
    trace_id: str | None = None
    records_processed: int | None = None
    checkpoint: str | None = None
    error: str | None = None


# Nodes that should have embeddings generated
EMBEDDING_NODE_TYPES = {"Artifact", "Memory"}


async def run_ingest(
    integration: str,
    tenant_ctx: TenantContext,
    full: bool = False,
) -> IngestStatusResponse:
    """Execute ingest for the given integration.

    Args:
        integration: Integration name (github, jira, slack).
        tenant_ctx: Authenticated tenant context.
        full: If True, ignore checkpoint and re-ingest all data.

    Returns:
        IngestStatusResponse with run results.

    Raises:
        HTTPException: For OAuth token not found, token expired, or internal errors.
    """
    tracer = _get_tracer()
    trace_id = get_current_trace_id()
    start_time = time.monotonic()

    # Emit start log
    emit_structured_log(
        StructuredLogRecord(
            event=EVENT.INGEST_RUN_STARTED,
            message=f"Ingest run started for {integration}",
            agent_identity="ingest-agent-v1",
            autonomy_level=2,
            tenant_id=tenant_ctx.tenant_id,
            duration_ms=0,
            trace_id=trace_id,
            metadata={"integration": integration, "full": full},
        )
    )

    span_name = "ingest.run"
    span_ctx = tracer.start_as_current_span(span_name) if tracer else None

    try:
        # Set OTEL span attributes
        if span_ctx:
            span = span_ctx.__enter__()  # type: ignore[attr-defined]
            span.set_attribute("context_os.agent_identity", "ingest-agent-v1")  # type: ignore[attr-defined]
            span.set_attribute("context_os.autonomy_level", 2)  # type: ignore[attr-defined]
            span.set_attribute("context_os.tenant_id", tenant_ctx.tenant_id)  # type: ignore[attr-defined]
            span.set_attribute(  # type: ignore[attr-defined]
                "context_os.input_summary",
                f"integration={integration} full={full}",
            )
            span.set_attribute("context_os.governance_markers", "{}")  # type: ignore[attr-defined]
            span.set_attribute("gen_ai.system", "context-os")  # type: ignore[attr-defined]
            span.set_attribute("gen_ai.operation.name", "ingest")  # type: ignore[attr-defined]

        # Load OAuth token
        factory = get_session_factory()
        async with factory() as session:
            token_repo = OAuthTokenRepository(session)
            token_row = await token_repo.get_for_tenant_integration(
                tenant_id=tenant_ctx.db_tenant_id,
                integration=integration,
            )

            if token_row is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "code": "not_configured",
                        "message": (
                            f"OAuth token for {integration}"
                            " not configured for this tenant"
                        ),
                    },
                )

            access_token = token_repo.decrypt_access_token(token_row)
            token_metadata = token_row.metadata_ or {}

        # Build adapter and run ingest
        nodes, final_cursor = await _run_adapter(
            integration=integration,
            tenant_ctx=tenant_ctx,
            access_token=access_token,
            token_metadata=token_metadata,
            full=full,
        )

        # Persist nodes to graph
        pool = get_age_pool()
        nodes_created = 0
        nodes_updated = 0
        embeddings_written = 0

        embedding_model = get_embedding_model()

        for node in nodes:
            node_type = node.get("node_type", "")
            # _age_label carries the Cypher label; fall back to node_type for
            # nodes that don't distinguish the two (e.g. demo/seed nodes).
            age_label = node.pop("_age_label", node_type)
            node_id_str = str(node.get("id", ""))

            try:
                await upsert_node(
                    pool=pool,
                    tenant_id=tenant_ctx.tenant_id,
                    node_type=age_label,
                    props=node,
                )
                nodes_created += 1
            except Exception as e:
                logger.warning("Failed to upsert node %s: %s", node_id_str, e)
                continue

            # Generate and store embeddings for Artifact/Memory nodes
            if node_type in EMBEDDING_NODE_TYPES:
                content = node.get("content", "") or node.get("title", "")
                if content and content.strip():
                    try:
                        embedding = embedding_model.encode(content)
                        await _upsert_embedding(
                            node_id=uuid.UUID(node_id_str),
                            tenant_id=tenant_ctx.db_tenant_id,
                            node_type=node_type,
                            content=content,
                            embedding=embedding,
                        )
                        embeddings_written += 1
                    except Exception as e:
                        logger.warning(
                            "Failed to write embedding for node %s: %s", node_id_str, e
                        )

        # Save checkpoint AFTER all commits succeed
        if final_cursor:
            factory2 = get_session_factory()
            async with factory2() as session2:
                ckpt_repo = CheckpointRepository(session2)
                await ckpt_repo.upsert(
                    tenant_id=tenant_ctx.db_tenant_id,
                    integration=integration,
                    object_type="all",
                    cursor_value=final_cursor,
                )
                await session2.commit()

            emit_structured_log(
                StructuredLogRecord(
                    event=EVENT.INGEST_RUN_CHECKPOINT_SAVED,
                    message=f"Checkpoint saved for {integration}",
                    agent_identity="ingest-agent-v1",
                    autonomy_level=2,
                    tenant_id=tenant_ctx.tenant_id,
                    duration_ms=(time.monotonic() - start_time) * 1000,
                    trace_id=trace_id,
                    metadata={"integration": integration, "cursor": final_cursor},
                )
            )

        duration_ms = (time.monotonic() - start_time) * 1000

        # Set output summary span attribute
        if span_ctx and tracer:
            try:
                span.set_attribute(  # type: ignore[attr-defined]
                    "context_os.output_summary",
                    (
                        f"records={len(nodes)} nodes_created={nodes_created}"
                        f" embeddings={embeddings_written}"
                    ),
                )
            except Exception:
                pass

        emit_structured_log(
            StructuredLogRecord(
                event=EVENT.INGEST_RUN_COMPLETED,
                message=f"Ingest run completed for {integration}",
                agent_identity="ingest-agent-v1",
                autonomy_level=2,
                tenant_id=tenant_ctx.tenant_id,
                duration_ms=duration_ms,
                trace_id=trace_id,
                metadata={
                    "integration": integration,
                    "records_fetched": len(nodes),
                    "nodes_created": nodes_created,
                    "nodes_updated": nodes_updated,
                    "edges_created": 0,
                    "checkpoint_cursor": final_cursor,
                },
            )
        )

        return IngestStatusResponse(
            status="completed",
            integration=integration,
            tenant_id=tenant_ctx.tenant_id,
            trace_id=trace_id,
            records_processed=len(nodes),
            checkpoint=final_cursor,
        )

    except TokenExpiredError as e:
        duration_ms = (time.monotonic() - start_time) * 1000
        emit_structured_log(
            StructuredLogRecord(
                event=EVENT.INGEST_SOURCE_TOKEN_EXPIRED,
                message=f"OAuth token expired for {integration}",
                agent_identity="ingest-agent-v1",
                autonomy_level=2,
                tenant_id=tenant_ctx.tenant_id,
                duration_ms=duration_ms,
                level="ERROR",
                trace_id=trace_id,
                metadata={"integration": integration, "error": str(e)},
            )
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.to_dict(),
        ) from e

    except HTTPException:
        raise

    except Exception as e:
        duration_ms = (time.monotonic() - start_time) * 1000
        emit_structured_log(
            StructuredLogRecord(
                event=EVENT.INGEST_RUN_FAILED,
                message=f"Ingest run failed for {integration}: {e}",
                agent_identity="ingest-agent-v1",
                autonomy_level=2,
                tenant_id=tenant_ctx.tenant_id,
                duration_ms=duration_ms,
                level="ERROR",
                trace_id=trace_id,
                metadata={"integration": integration, "error": str(e)},
            )
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "ingest_error",
                "message": f"Ingest failed: {e}",
                "trace_id": trace_id,
            },
        ) from e

    finally:
        if span_ctx:
            try:
                span_ctx.__exit__(None, None, None)  # type: ignore[attr-defined]
            except Exception:
                pass


async def _run_adapter(
    integration: str,
    tenant_ctx: TenantContext,
    access_token: str,
    token_metadata: dict[str, Any],
    full: bool,
) -> tuple[list[dict[str, Any]], str | None]:
    """Instantiate the correct adapter and run ingest.

    Args:
        integration: Integration name.
        tenant_ctx: Tenant context.
        access_token: Decrypted OAuth token.
        token_metadata: Token metadata dict from DB.
        full: Full sync flag.

    Returns:
        Tuple of (normalized_nodes, final_cursor).
    """
    if integration == "github":
        return await _run_github_ingest(tenant_ctx, access_token, full)
    elif integration == "jira":
        cloud_id = token_metadata.get("cloud_id")
        cloud_id_str = str(cloud_id) if cloud_id else None
        return await _run_jira_ingest(tenant_ctx, access_token, cloud_id_str, full)
    elif integration == "slack":
        return await _run_slack_ingest(tenant_ctx, access_token, full)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "invalid_integration",
                "message": f"Unknown integration: {integration}",
            },
        )


async def _run_github_ingest(
    tenant_ctx: TenantContext,
    access_token: str,
    full: bool,
) -> tuple[list[dict[str, Any]], str | None]:
    """Run GitHub ingest using the GitHubClient and GitHubNormalizer."""
    from datetime import UTC, datetime

    from context_os.ingestion.github.client import GitHubClient
    from context_os.ingestion.github.normalizer import GitHubNormalizer

    normalizer = GitHubNormalizer(tenant_id=tenant_ctx.tenant_id)
    nodes: list[dict[str, Any]] = []

    async with GitHubClient(access_token=access_token) as client:
        repos = await client.list_repos()
        for repo in repos:
            repo_node = normalizer.repo_to_initiative(repo)
            nodes.append(repo_node)

            repo_name = repo.get("full_name", "")
            if not repo_name:
                continue

            # Milestones → Goals
            try:
                milestones = await client.list_milestones(repo_name)
                for m in milestones:
                    nodes.append(normalizer.milestone_to_goal(m, repo_name))
            except Exception as e:
                logger.warning("Failed to fetch milestones for %s: %s", repo_name, e)

            # Pull Requests → Artifacts
            try:
                prs = await client.list_pulls(repo_name)
                for pr in prs:
                    nodes.append(normalizer.pr_to_artifact(pr, repo_name))
            except Exception as e:
                logger.warning("Failed to fetch PRs for %s: %s", repo_name, e)

            # Issues → Signal or Artifact
            try:
                issues = await client.list_issues(repo_name)
                for issue in issues:
                    nodes.append(
                        normalizer.issue_to_signal_or_artifact(issue, repo_name)
                    )
            except Exception as e:
                logger.warning("Failed to fetch issues for %s: %s", repo_name, e)

    cursor = datetime.now(UTC).isoformat() + "Z"
    return nodes, cursor


async def _run_jira_ingest(
    tenant_ctx: TenantContext,
    access_token: str,
    cloud_id: str | None,
    full: bool,
) -> tuple[list[dict[str, Any]], str | None]:
    """Run Jira ingest using the JiraClient and JiraNomalizer."""
    from datetime import UTC, datetime

    from context_os.ingestion.jira.client import JiraClient
    from context_os.ingestion.jira.normalizer import JiraNomalizer

    normalizer = JiraNomalizer(tenant_id=tenant_ctx.tenant_id)
    nodes: list[dict[str, Any]] = []

    async with JiraClient(access_token=access_token, cloud_id=cloud_id) as client:
        # Projects → Initiatives
        try:
            projects = await client.list_projects()
            for proj in projects:
                nodes.append(normalizer.project_to_initiative(proj))
        except Exception as e:
            logger.warning("Failed to fetch Jira projects: %s", e)

        # Epics → Goals
        try:
            epics = await client.list_epics()
            for epic in epics:
                nodes.append(normalizer.epic_to_goal(epic))
        except Exception as e:
            logger.warning("Failed to fetch Jira epics: %s", e)

        # Issues
        try:
            issues, _ = await client.search_issues(
                "project IS NOT EMPTY ORDER BY updated DESC"
            )
            for issue in issues:
                nodes.append(normalizer.issue_to_signal_or_artifact(issue))
        except Exception as e:
            logger.warning("Failed to fetch Jira issues: %s", e)

    cursor = datetime.now(UTC).isoformat() + "Z"
    return nodes, cursor


async def _run_slack_ingest(
    tenant_ctx: TenantContext,
    access_token: str,
    full: bool,
) -> tuple[list[dict[str, Any]], str | None]:
    """Run Slack ingest using the SlackClient and SlackNormalizer."""
    from context_os.config import get_settings
    from context_os.graph.client import get_age_pool
    from context_os.graph.mutations import upsert_pending_edge
    from context_os.ingestion.slack.client import SlackClient
    from context_os.ingestion.slack.normalizer import SlackNormalizer

    settings = get_settings()
    channel_ids = settings.slack_channel_ids_list
    normalizer = SlackNormalizer(tenant_id=tenant_ctx.tenant_id)
    nodes: list[dict[str, Any]] = []
    last_ts: str | None = None

    async with SlackClient(bot_token=access_token) as client:
        for channel_id in channel_ids:
            try:
                messages, _ = await client.list_messages(channel_id=channel_id)
                for msg in messages:
                    signal_node = normalizer.message_to_signal(msg, channel_id)
                    nodes.append(signal_node)

                    # Track newest ts for incremental cursor
                    ts = msg.get("ts", "")
                    if ts and (last_ts is None or ts > last_ts):
                        last_ts = ts

                    # Extract and record pending GitHub PR references
                    text = msg.get("text", "")
                    pr_refs = normalizer.extract_github_pr_refs(text)
                    if pr_refs:
                        pool = get_age_pool()
                        for pr_url in pr_refs:
                            try:
                                await upsert_pending_edge(
                                    pool=pool,
                                    tenant_id=tenant_ctx.tenant_id,
                                    from_id=str(signal_node["id"]),
                                    to_source_id=pr_url,
                                    to_source="github",
                                    dependency_type="references",
                                )
                            except Exception as e:
                                logger.warning("Failed to create pending edge: %s", e)
            except Exception as e:
                logger.warning(
                    "Failed to fetch messages from channel %s: %s", channel_id, e
                )

    return nodes, last_ts


async def _upsert_embedding(
    node_id: uuid.UUID,
    tenant_id: uuid.UUID,
    node_type: str,
    content: str,
    embedding: list[float],
) -> None:
    """Upsert a node embedding to the node_embeddings table.

    Args:
        node_id: Node UUID (matches AGE graph node id).
        tenant_id: Internal tenant UUID.
        node_type: Node type string.
        content: Text that was embedded.
        embedding: 768-dim normalized embedding vector.
    """
    from datetime import UTC, datetime

    from sqlalchemy.dialects.postgresql import insert

    from context_os.db.engine import get_session_factory
    from context_os.db.models import NodeEmbedding

    factory = get_session_factory()
    async with factory() as session:
        stmt = (
            insert(NodeEmbedding)
            .values(
                id=node_id,
                tenant_id=tenant_id,
                node_type=node_type,
                content=content,
                embedding=embedding,
                updated_at=datetime.now(UTC),
            )
            .on_conflict_do_update(
                index_elements=["id"],
                set_={
                    "content": content,
                    "embedding": embedding,
                    "updated_at": datetime.now(UTC),
                },
            )
        )
        await session.execute(stmt)
        await session.commit()


@router.post("/{integration}", response_model=IngestStatusResponse, status_code=202)
async def trigger_ingest(
    integration: str,
    full: bool = Query(default=False, description="Full re-ingest ignoring checkpoint"),
    tenant: TenantContext = Depends(get_current_tenant),
) -> IngestStatusResponse:
    """Trigger incremental ingest for a source integration.

    Args:
        integration: Integration name (github, jira, slack).
        full: If True, ignore checkpoint and re-ingest all data.
        tenant: Authenticated tenant context.

    Returns:
        202 Accepted with initial ingest status.
    """
    if integration not in ("github", "jira", "slack"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "invalid_integration",
                "message": f"Unknown integration: {integration}",
            },
        )

    return await run_ingest(integration=integration, tenant_ctx=tenant, full=full)


@router.get("/{integration}/status", response_model=IngestStatusResponse)
async def get_ingest_status(
    integration: str,
    tenant: TenantContext = Depends(get_current_tenant),
) -> IngestStatusResponse:
    """Get last ingest run status and checkpoint for an integration.

    Args:
        integration: Integration name (github, jira, slack).
        tenant: Authenticated tenant context.

    Returns:
        Last ingest checkpoint status.
    """
    factory = get_session_factory()
    async with factory() as session:
        repo = CheckpointRepository(session)
        checkpoint = await repo.get(
            tenant_id=tenant.db_tenant_id,
            integration=integration,
            object_type="all",
        )

    return IngestStatusResponse(
        status="checkpoint_saved" if checkpoint else "no_checkpoint",
        integration=integration,
        tenant_id=tenant.tenant_id,
        checkpoint=checkpoint.cursor_value if checkpoint else None,
    )
