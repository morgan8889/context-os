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
from context_os.db.models import OAuthToken, SyncCheckpoint, Tenant


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
