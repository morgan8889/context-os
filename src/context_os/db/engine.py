"""SQLAlchemy 2.0 async engine and session factory.

Registers pgvector asyncpg codec via sync_engine connect event so that
Vector columns are transparently serialized/deserialized.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from pgvector.asyncpg import register_vector
from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from context_os.config import get_settings

_engine: AsyncEngine | None = None
_async_session_factory: async_sessionmaker[AsyncSession] | None = None


def _register_pgvector_codec(dbapi_conn: object, _connection_record: object) -> None:
    """Register pgvector codec on each new sync connection.

    Called via SQLAlchemy sync_engine connect event. The asyncpg codec
    is required for Vector column reads and writes to work correctly.
    """
    import asyncio

    async def _register(conn: object) -> None:
        await register_vector(conn)  # type: ignore[arg-type]

    asyncio.get_event_loop().run_until_complete(_register(dbapi_conn))


async def init_db() -> None:
    """Initialize the async engine and session factory.

    Creates a connection pool backed by asyncpg. The pgvector codec is
    registered via the sync_engine connect event fired on first connection.

    Must be called once at application startup (FastAPI lifespan).
    """
    global _engine, _async_session_factory

    settings = get_settings()
    _engine = create_async_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        echo=False,
    )

    # Register pgvector codec on new sync-layer connections
    event.listen(_engine.sync_engine, "connect", _register_pgvector_codec)

    _async_session_factory = async_sessionmaker(
        bind=_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


async def close_db() -> None:
    """Dispose the connection pool.

    Must be called at application shutdown (FastAPI lifespan).
    """
    global _engine, _async_session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _async_session_factory = None


def get_engine() -> AsyncEngine:
    """Return the initialized async engine.

    Raises:
        RuntimeError: If init_db() has not been called.
    """
    if _engine is None:
        raise RuntimeError("Database engine not initialized; call init_db() first")
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return the session factory.

    Raises:
        RuntimeError: If init_db() has not been called.
    """
    if _async_session_factory is None:
        raise RuntimeError("Session factory not initialized; call init_db() first")
    return _async_session_factory


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: yield a database session, rolling back on error.

    Usage:
        @router.get("/")
        async def handler(session: AsyncSession = Depends(get_session)):
            ...
    """
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
