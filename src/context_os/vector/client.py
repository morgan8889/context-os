"""pgvector-aware SQLAlchemy session helper and codec registration.

The pgvector asyncpg codec must be registered once per engine connection
so that Vector(768) columns are correctly serialized/deserialized.
"""

from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

logger = logging.getLogger(__name__)


def register_pgvector_codec(engine: AsyncEngine) -> None:
    """Register the pgvector asyncpg codec on the sync engine's connect event.

    Must be called once after engine creation. The codec enables transparent
    Vector(768) serialization/deserialization via asyncpg.

    Args:
        engine: The SQLAlchemy async engine to register the codec on.
    """
    import asyncio

    from pgvector.asyncpg import register_vector
    from sqlalchemy import event

    def _on_connect(dbapi_conn: object, _record: object) -> None:
        """Register vector codec on each new connection."""

        async def _register(conn: object) -> None:
            await register_vector(conn)  # type: ignore[arg-type]

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # In async context, schedule as a task
                import asyncio as _asyncio

                _asyncio.ensure_future(_register(dbapi_conn))
            else:
                loop.run_until_complete(_register(dbapi_conn))
        except Exception as e:
            logger.warning("Failed to register pgvector codec: %s", e)

    event.listen(engine.sync_engine, "connect", _on_connect)
    logger.debug("pgvector asyncpg codec registration hook installed")


class VectorSessionHelper:
    """Async context manager helper for pgvector-aware SQLAlchemy sessions.

    Wraps an AsyncSession factory to provide a clean context manager
    interface for vector search operations.

    Usage:
        async with VectorSessionHelper(session_factory) as session:
            results = await search(session, tenant_id, query, k=5)
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with an existing async session.

        Args:
            session: SQLAlchemy async session to wrap.
        """
        self._session = session

    async def __aenter__(self) -> AsyncSession:
        return self._session

    async def __aexit__(
        self, exc_type: object, exc_val: object, exc_tb: object
    ) -> None:
        if exc_type is not None:
            await self._session.rollback()
        else:
            await self._session.commit()
