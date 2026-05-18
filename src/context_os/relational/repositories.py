"""Relational repositories for tenant, OAuth token, and checkpoint management.

All repositories enforce tenant scoping. OAuthTokenRepository encrypts/decrypts
tokens using Fernet AES-256 before storage and after retrieval.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from cryptography.fernet import Fernet
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from context_os.config import get_settings
from context_os.core.errors import TenantIsolationError
from context_os.db.models import (
    ApprovalItem,
    BriefingRun,
    EvalRun,
    GoldenDataset,
    OAuthToken,
    SyncCheckpoint,
    Tenant,
)


def _get_fernet() -> Fernet:
    """Return a Fernet cipher from the ENCRYPTION_KEY setting."""
    settings = get_settings()
    return Fernet(settings.encryption_key.encode())


def _assert_tenant_id(tenant_id: str | uuid.UUID | None) -> None:
    """Raise TenantIsolationError if tenant_id is empty or None.

    Args:
        tenant_id: Tenant identifier to validate.

    Raises:
        TenantIsolationError: If tenant_id is falsy or empty string.
    """
    if not tenant_id:
        raise TenantIsolationError(
            code="tenant_isolation_error",
            message="tenant_id is required for all data operations",
        )


class TenantRepository:
    """CRUD operations for Tenant records.

    All queries are tenant-scoped — no cross-tenant data access is possible
    through this repository.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, clerk_org_id: str, name: str) -> Tenant:
        """Create a new tenant record.

        Args:
            clerk_org_id: Clerk organization ID from JWT.
            name: Human-readable organization name.

        Returns:
            The created Tenant ORM instance.
        """
        tenant = Tenant(
            id=uuid.uuid4(),
            clerk_org_id=clerk_org_id,
            name=name,
            created_at=datetime.now(UTC),
        )
        self._session.add(tenant)
        await self._session.flush()
        return tenant

    async def get_by_clerk_org_id(self, clerk_org_id: str) -> Tenant | None:
        """Look up a tenant by Clerk org ID.

        Args:
            clerk_org_id: The org ID from the JWT o.id claim.

        Returns:
            Tenant instance or None if not found.
        """
        stmt = select(Tenant).where(Tenant.clerk_org_id == clerk_org_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, tenant_id: uuid.UUID) -> Tenant | None:
        """Look up a tenant by its internal UUID.

        Args:
            tenant_id: The internal UUID primary key.

        Returns:
            Tenant instance or None if not found.
        """
        stmt = select(Tenant).where(Tenant.id == tenant_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()


class OAuthTokenRepository:
    """Encrypted storage for OAuth tokens per tenant per integration.

    Tokens are encrypted with Fernet AES-256 before storage and decrypted
    on retrieval. The raw token value is never persisted to the database.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._fernet = _get_fernet()

    def _encrypt(self, value: str) -> bytes:
        """Fernet-encrypt a token string."""
        return self._fernet.encrypt(value.encode())

    def _decrypt(self, value: bytes) -> str:
        """Fernet-decrypt token bytes to a string."""
        return self._fernet.decrypt(value).decode()

    async def upsert(
        self,
        tenant_id: uuid.UUID,
        integration: str,
        access_token: str,
        refresh_token: str | None = None,
        expires_at: datetime | None = None,
        scope: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> OAuthToken:
        """Create or update an OAuth token for a tenant/integration pair.

        Args:
            tenant_id: Internal tenant UUID (must be non-empty).
            integration: Integration name (github | jira | slack).
            access_token: Plaintext access token to encrypt and store.
            refresh_token: Optional plaintext refresh token.
            expires_at: Optional expiry timestamp.
            scope: OAuth scope string.
            metadata: Integration-specific metadata (cloudId, etc.).

        Returns:
            The upserted OAuthToken instance.

        Raises:
            TenantIsolationError: If tenant_id is empty.
        """
        _assert_tenant_id(str(tenant_id))

        access_enc = self._encrypt(access_token)
        refresh_enc = self._encrypt(refresh_token) if refresh_token else None

        stmt = (
            insert(OAuthToken)
            .values(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                integration=integration,
                access_token_enc=access_enc,
                refresh_token_enc=refresh_enc,
                expires_at=expires_at,
                scope=scope,
                metadata=metadata,
                updated_at=datetime.now(UTC),
            )
            .on_conflict_do_update(
                constraint="uq_oauth_tokens_tenant_integration",
                set_={
                    "access_token_enc": access_enc,
                    "refresh_token_enc": refresh_enc,
                    "expires_at": expires_at,
                    "scope": scope,
                    "metadata": metadata,
                    "updated_at": datetime.now(UTC),
                },
            )
            .returning(OAuthToken)
        )
        result = await self._session.execute(stmt)
        row = result.fetchone()
        if row is None:
            raise RuntimeError("Upsert returned no row")
        return row[0]

    async def get_for_tenant_integration(
        self,
        tenant_id: uuid.UUID,
        integration: str,
    ) -> OAuthToken | None:
        """Retrieve the OAuth token row for a tenant/integration pair.

        The returned token fields are still encrypted — use decrypt_access_token()
        to get the plaintext value.

        Args:
            tenant_id: Internal tenant UUID.
            integration: Integration name.

        Returns:
            OAuthToken instance (with encrypted fields) or None if not configured.

        Raises:
            TenantIsolationError: If tenant_id is empty.
        """
        _assert_tenant_id(str(tenant_id))

        stmt = select(OAuthToken).where(
            OAuthToken.tenant_id == tenant_id,
            OAuthToken.integration == integration,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    def decrypt_access_token(self, token: OAuthToken) -> str:
        """Decrypt and return the plaintext access token.

        Args:
            token: OAuthToken ORM instance.

        Returns:
            Plaintext access token string.
        """
        return self._decrypt(token.access_token_enc)

    def decrypt_refresh_token(self, token: OAuthToken) -> str | None:
        """Decrypt and return the plaintext refresh token, or None.

        Args:
            token: OAuthToken ORM instance.

        Returns:
            Plaintext refresh token string or None if not set.
        """
        if token.refresh_token_enc is None:
            return None
        return self._decrypt(token.refresh_token_enc)


class ApprovalItemRepository:
    """CRUD operations for ApprovalItem records.

    All queries are scoped to tenant_id. Status transitions are:
        pending → approved (via update_approval)
        pending → rejected (via update_rejection)
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        tenant_id: str,
        item_type: str,
        content: dict[str, Any],
        failure_flags: dict[str, Any] | None = None,
        run_id: uuid.UUID | None = None,
        workflow_thread_id: str | None = None,
    ) -> ApprovalItem:
        """Create a new pending ApprovalItem.

        Args:
            tenant_id: Clerk org ID — all items must be tenant-scoped.
            item_type: briefing_draft | proposed_dependency | proposed_risk.
            content: Item-type-specific JSONB payload.
            failure_flags: Optional list of detected failure mode dicts.
            run_id: FK to briefing_runs.id for briefing_draft items.
            workflow_thread_id: LangGraph thread ID for interrupt/resume.

        Returns:
            The created ApprovalItem ORM instance.

        Raises:
            TenantIsolationError: If tenant_id is empty.
        """
        _assert_tenant_id(tenant_id)
        now = datetime.now(UTC)
        item = ApprovalItem(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            item_type=item_type,
            status="pending",
            content=content,
            failure_flags=failure_flags,
            created_at=now,
            updated_at=now,
            run_id=run_id,
            workflow_thread_id=workflow_thread_id,
        )
        self._session.add(item)
        await self._session.flush()
        return item

    async def get_by_id(
        self,
        item_id: uuid.UUID,
        tenant_id: str,
    ) -> ApprovalItem | None:
        """Retrieve an ApprovalItem by ID, scoped to tenant.

        Args:
            item_id: UUID primary key.
            tenant_id: Clerk org ID for tenant isolation.

        Returns:
            ApprovalItem or None if not found.
        """
        stmt = select(ApprovalItem).where(
            ApprovalItem.id == item_id,
            ApprovalItem.tenant_id == tenant_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_tenant(
        self,
        tenant_id: str,
        status: str | None = None,
        item_type: str | None = None,
        stale_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ApprovalItem]:
        """List ApprovalItems for a tenant with optional filters.

        Args:
            tenant_id: Clerk org ID.
            status: Optional filter — pending | approved | rejected.
            item_type: Optional item type filter.
            stale_only: If True, only return items pending > 24 hours.
            limit: Maximum number of items to return.
            offset: Pagination offset.

        Returns:
            List of ApprovalItem instances ordered by created_at DESC.
        """
        from sqlalchemy import and_

        _assert_tenant_id(tenant_id)

        conditions = [ApprovalItem.tenant_id == tenant_id]
        if status:
            conditions.append(ApprovalItem.status == status)
        if item_type:
            conditions.append(ApprovalItem.item_type == item_type)
        if stale_only:
            from datetime import timedelta

            stale_threshold = datetime.now(UTC) - timedelta(hours=24)
            conditions.append(
                and_(
                    ApprovalItem.status == "pending",
                    ApprovalItem.created_at < stale_threshold,
                )
            )

        stmt = (
            select(ApprovalItem)
            .where(*conditions)
            .order_by(ApprovalItem.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_status(
        self,
        item_id: uuid.UUID,
        tenant_id: str,
        status: str,
    ) -> ApprovalItem | None:
        """Update an ApprovalItem's status.

        Args:
            item_id: UUID primary key.
            tenant_id: Clerk org ID for tenant isolation.
            status: New status value.

        Returns:
            Updated ApprovalItem or None if not found.
        """
        item = await self.get_by_id(item_id, tenant_id)
        if item is None:
            return None
        item.status = status
        item.updated_at = datetime.now(UTC)
        await self._session.flush()
        return item

    async def update_approval(
        self,
        item_id: uuid.UUID,
        tenant_id: str,
        operator_id: str,
        graph_node_id: uuid.UUID | None = None,
        edit_delta: dict[str, Any] | None = None,
    ) -> ApprovalItem | None:
        """Record an approval action on an ApprovalItem.

        Args:
            item_id: UUID primary key.
            tenant_id: Clerk org ID.
            operator_id: Clerk user ID of the approving operator.
            graph_node_id: UUID of the promoted graph node (if applicable).
            edit_delta: Token diff metadata if the content was edited before approval.

        Returns:
            Updated ApprovalItem or None if not found.
        """
        item = await self.get_by_id(item_id, tenant_id)
        if item is None:
            return None
        now = datetime.now(UTC)
        item.status = "approved"
        item.operator_id = operator_id
        item.acted_at = now
        item.updated_at = now
        item.graph_node_id = graph_node_id
        if edit_delta is not None:
            item.edit_delta = edit_delta
        await self._session.flush()
        return item

    async def update_rejection(
        self,
        item_id: uuid.UUID,
        tenant_id: str,
        operator_id: str,
        reason: str | None = None,
    ) -> ApprovalItem | None:
        """Record a rejection action on an ApprovalItem.

        Args:
            item_id: UUID primary key.
            tenant_id: Clerk org ID.
            operator_id: Clerk user ID of the rejecting operator.
            reason: Optional human-readable rejection reason.

        Returns:
            Updated ApprovalItem or None if not found.
        """
        item = await self.get_by_id(item_id, tenant_id)
        if item is None:
            return None
        now = datetime.now(UTC)
        item.status = "rejected"
        item.operator_id = operator_id
        item.acted_at = now
        item.updated_at = now
        item.rejection_reason = reason
        await self._session.flush()
        return item


class BriefingRunRepository:
    """CRUD operations for BriefingRun records.

    Each BriefingRun tracks one briefing generation attempt.
    Status transitions: generating → complete | failed | partial.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        tenant_id: str,
        trigger_type: str,
        window_days: int,
        window_start: datetime,
        window_end: datetime,
    ) -> BriefingRun:
        """Create a new BriefingRun in generating state.

        Args:
            tenant_id: Clerk org ID.
            trigger_type: manual | scheduled.
            window_days: Number of days in the briefing window.
            window_start: Start of the data window.
            window_end: End of the data window.

        Returns:
            The created BriefingRun ORM instance.
        """
        _assert_tenant_id(tenant_id)
        run = BriefingRun(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            trigger_type=trigger_type,
            window_days=window_days,
            window_start=window_start,
            window_end=window_end,
            status="generating",
            created_at=datetime.now(UTC),
        )
        self._session.add(run)
        await self._session.flush()
        return run

    async def get_by_id(
        self,
        run_id: uuid.UUID,
        tenant_id: str,
    ) -> BriefingRun | None:
        """Retrieve a BriefingRun by ID, scoped to tenant.

        Args:
            run_id: UUID primary key.
            tenant_id: Clerk org ID.

        Returns:
            BriefingRun or None if not found.
        """
        stmt = select(BriefingRun).where(
            BriefingRun.id == run_id,
            BriefingRun.tenant_id == tenant_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_for_tenant(self, tenant_id: str) -> BriefingRun | None:
        """Return the most recent generating BriefingRun for a tenant.

        Used to prevent concurrent runs (returns most recent generating run).

        Args:
            tenant_id: Clerk org ID.

        Returns:
            Active BriefingRun or None if no run is currently generating.
        """
        stmt = (
            select(BriefingRun)
            .where(
                BriefingRun.tenant_id == tenant_id,
                BriefingRun.status == "generating",
            )
            .order_by(BriefingRun.created_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_status(
        self,
        run_id: uuid.UUID,
        tenant_id: str,
        status: str,
        cost_tokens: int | None = None,
        latency_ms: int | None = None,
        error_detail: str | None = None,
        approval_item_id: uuid.UUID | None = None,
        input_signal_counts: dict[str, Any] | None = None,
        retrieval_hit_rate: float | None = None,
    ) -> BriefingRun | None:
        """Update a BriefingRun's status and optional metrics.

        Args:
            run_id: UUID primary key.
            tenant_id: Clerk org ID.
            status: New status (complete | failed | partial).
            cost_tokens: Total token cost for this run.
            latency_ms: Total latency in milliseconds.
            error_detail: Error message if status=failed.
            approval_item_id: FK to the created ApprovalItem.
            input_signal_counts: Signal counts by source.
            retrieval_hit_rate: Retrieval hit rate.

        Returns:
            Updated BriefingRun or None if not found.
        """
        run = await self.get_by_id(run_id, tenant_id)
        if run is None:
            return None
        run.status = status
        run.completed_at = datetime.now(UTC)
        if cost_tokens is not None:
            run.cost_tokens = cost_tokens
        if latency_ms is not None:
            run.latency_ms = latency_ms
        if error_detail is not None:
            run.error_detail = error_detail
        if approval_item_id is not None:
            run.approval_item_id = approval_item_id
        if input_signal_counts is not None:
            run.input_signal_counts = input_signal_counts
        if retrieval_hit_rate is not None:
            run.retrieval_hit_rate = retrieval_hit_rate  # type: ignore[assignment]
        await self._session.flush()
        return run


class EvalRunRepository:
    """CRUD operations for EvalRun records.

    Stores results from synthesizer and mapper evaluation suite runs.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        tenant_id: str,
        eval_type: str,
        dataset_version: str,
        dataset_id: uuid.UUID | None = None,
        status: str = "running",
        scores: dict[str, Any] | None = None,
        gates_passed: bool | None = None,
        compared_to_run_id: uuid.UUID | None = None,
        score_deltas: dict[str, Any] | None = None,
        duration_ms: int | None = None,
        error_detail: str | None = None,
    ) -> EvalRun:
        """Create a new EvalRun record.

        Args:
            tenant_id: Clerk org ID.
            eval_type: synthesizer | mapper.
            dataset_version: Version string of the dataset.
            dataset_id: Optional FK to golden_datasets.id.
            status: Initial status (default "running").
            scores: Initial scores dict (default empty).
            gates_passed: Whether CI gates passed.
            compared_to_run_id: Optional FK to previous run for delta computation.
            score_deltas: Optional score delta dict vs prior run.
            duration_ms: Optional eval duration in milliseconds.
            error_detail: Optional error message.

        Returns:
            The created EvalRun ORM instance.
        """
        _assert_tenant_id(tenant_id)
        run = EvalRun(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            eval_type=eval_type,
            dataset_id=dataset_id,
            dataset_version=dataset_version,
            status=status,
            scores=scores or {},
            gates_passed=gates_passed,
            compared_to_run_id=compared_to_run_id,
            score_deltas=score_deltas,
            duration_ms=duration_ms,
            error_detail=error_detail,
            created_at=datetime.now(UTC),
        )
        self._session.add(run)
        await self._session.flush()
        return run

    async def get_by_id(
        self,
        run_id: uuid.UUID,
        tenant_id: str,
    ) -> EvalRun | None:
        """Retrieve an EvalRun by ID, scoped to tenant.

        Args:
            run_id: UUID primary key.
            tenant_id: Clerk org ID.

        Returns:
            EvalRun or None if not found.
        """
        stmt = select(EvalRun).where(
            EvalRun.id == run_id,
            EvalRun.tenant_id == tenant_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_tenant(
        self,
        tenant_id: str,
        eval_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[EvalRun]:
        """List EvalRuns for a tenant, most recent first.

        Args:
            tenant_id: Clerk org ID.
            eval_type: Optional filter by synthesizer | mapper.
            limit: Maximum results.
            offset: Pagination offset.

        Returns:
            List of EvalRun instances ordered by created_at DESC.
        """
        _assert_tenant_id(tenant_id)
        conditions = [EvalRun.tenant_id == tenant_id]
        if eval_type:
            conditions.append(EvalRun.eval_type == eval_type)
        stmt = (
            select(EvalRun)
            .where(*conditions)
            .order_by(EvalRun.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_scores(
        self,
        run_id: uuid.UUID,
        tenant_id: str,
        status: str,
        scores: dict[str, Any],
        gates_passed: bool,
        score_deltas: dict[str, Any] | None = None,
        duration_ms: int | None = None,
        error_detail: str | None = None,
    ) -> EvalRun | None:
        """Update an EvalRun with computed scores and gate results.

        Args:
            run_id: UUID primary key.
            tenant_id: Clerk org ID.
            status: passed | failed | error.
            scores: Computed metric scores dict.
            gates_passed: True if all CI gates cleared.
            score_deltas: Optional deltas vs compared_to_run_id.
            duration_ms: Total eval duration.
            error_detail: Error message if status=error.

        Returns:
            Updated EvalRun or None if not found.
        """
        run = await self.get_by_id(run_id, tenant_id)
        if run is None:
            return None
        run.status = status
        run.scores = scores
        run.gates_passed = gates_passed
        run.completed_at = datetime.now(UTC)
        if score_deltas is not None:
            run.score_deltas = score_deltas
        if duration_ms is not None:
            run.duration_ms = duration_ms
        if error_detail is not None:
            run.error_detail = error_detail
        await self._session.flush()
        return run


class GoldenDatasetRepository:
    """CRUD operations for GoldenDataset records.

    Manages versioned ground-truth datasets for eval suites.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        tenant_id: str,
        dataset_type: str,
        version: str,
        content: dict[str, Any],
        record_count: int,
        description: str | None = None,
        built_from_approval_items: list[Any] | dict[str, Any] | None = None,
    ) -> GoldenDataset:
        """Create a new GoldenDataset.

        Args:
            tenant_id: Clerk org ID.
            dataset_type: synthesizer | mapper.
            version: Semantic version string (e.g. '1.0.0').
            content: Array of records serialized as JSONB.
            record_count: Number of records in content.
            description: Human-readable description of this dataset.
            built_from_approval_items: List of approval_item UUID strings used.

        Returns:
            The created GoldenDataset ORM instance.

        Raises:
            TenantIsolationError: If tenant_id is empty.
        """
        _assert_tenant_id(tenant_id)
        dataset = GoldenDataset(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            dataset_type=dataset_type,
            version=version,
            description=description,
            record_count=record_count,
            content=content,
            created_at=datetime.now(UTC),
            built_from_approval_items=built_from_approval_items,
        )
        self._session.add(dataset)
        await self._session.flush()
        return dataset

    async def get_by_id(
        self,
        dataset_id: uuid.UUID,
        tenant_id: str,
    ) -> GoldenDataset | None:
        """Retrieve a GoldenDataset by ID, scoped to tenant.

        Args:
            dataset_id: UUID primary key.
            tenant_id: Clerk org ID.

        Returns:
            GoldenDataset or None if not found.
        """
        stmt = select(GoldenDataset).where(
            GoldenDataset.id == dataset_id,
            GoldenDataset.tenant_id == tenant_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_latest_by_type(
        self,
        dataset_type: str,
        tenant_id: str | None = None,
    ) -> GoldenDataset | None:
        """Return the most recently created GoldenDataset for a type (and optionally tenant).

        Args:
            dataset_type: synthesizer | mapper.
            tenant_id: Optional Clerk org ID — if provided, scopes to that tenant.

        Returns:
            The newest GoldenDataset or None if none exist.
        """
        conditions = [GoldenDataset.dataset_type == dataset_type]
        if tenant_id:
            conditions.append(GoldenDataset.tenant_id == tenant_id)
        stmt = (
            select(GoldenDataset)
            .where(*conditions)
            .order_by(GoldenDataset.created_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()


class CheckpointRepository:
    """Sync checkpoint CRUD for incremental ingestion.

    Checkpoints are ONLY updated after a successful DB commit — never after
    a fetch or normalize step. Callers are responsible for commit ordering.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(
        self,
        tenant_id: uuid.UUID,
        integration: str,
        object_type: str,
    ) -> SyncCheckpoint | None:
        """Retrieve the last checkpoint cursor for a (tenant, integration, object_type).

        Args:
            tenant_id: Internal tenant UUID.
            integration: Integration name.
            object_type: Object type (issues, prs, messages, etc.).

        Returns:
            SyncCheckpoint instance or None if no checkpoint saved yet.

        Raises:
            TenantIsolationError: If tenant_id is empty.
        """
        _assert_tenant_id(str(tenant_id))

        stmt = select(SyncCheckpoint).where(
            SyncCheckpoint.tenant_id == tenant_id,
            SyncCheckpoint.integration == integration,
            SyncCheckpoint.object_type == object_type,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert(
        self,
        tenant_id: uuid.UUID,
        integration: str,
        object_type: str,
        cursor_value: str | None,
    ) -> SyncCheckpoint:
        """Create or update a sync checkpoint.

        MUST only be called after a successful DB commit that persists the
        corresponding graph/relational writes. This ensures checkpoint
        accuracy and prevents re-ingesting already-committed data.

        Args:
            tenant_id: Internal tenant UUID.
            integration: Integration name.
            object_type: Object type.
            cursor_value: New cursor (ISO timestamp, nextPageToken, Slack ts).

        Returns:
            Upserted SyncCheckpoint instance.

        Raises:
            TenantIsolationError: If tenant_id is empty.
        """
        _assert_tenant_id(str(tenant_id))

        stmt = (
            insert(SyncCheckpoint)
            .values(
                tenant_id=tenant_id,
                integration=integration,
                object_type=object_type,
                cursor_value=cursor_value,
                updated_at=datetime.now(UTC),
            )
            .on_conflict_do_update(
                constraint="pk_sync_checkpoints",
                set_={
                    "cursor_value": cursor_value,
                    "updated_at": datetime.now(UTC),
                },
            )
            .returning(SyncCheckpoint)
        )
        result = await self._session.execute(stmt)
        row = result.fetchone()
        if row is None:
            raise RuntimeError("Checkpoint upsert returned no row")
        return row[0]
