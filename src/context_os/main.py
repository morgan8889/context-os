"""FastAPI application factory with lifespan management.

All infrastructure (DB, AGE pool, OTEL tracer) is initialized in the lifespan
context manager to ensure clean startup/shutdown ordering.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from context_os.config import get_settings
from context_os.core.errors import (
    AuthError,
    ContextOSError,
    TenantIsolationError,
    ValidationError,
)
from context_os.db.engine import close_db, init_db
from context_os.graph.client import close_age_pool, create_age_pool, init_graph
from context_os.observability.langfuse import configure_langfuse_env
from context_os.observability.tracer import init_tracer, instrument_app

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: initialize and teardown all infrastructure.

    Startup order:
    1. Configure Langfuse environment variables
    2. Initialize OTEL tracer (registers Langfuse span processor)
    3. Initialize SQLAlchemy async engine + pgvector codec
    4. Create AGE asyncpg pool
    5. Initialize AGE graph (create if not exists)
    6. Instrument FastAPI app with OTEL auto-instrumentation

    Shutdown order (reverse):
    - Close AGE pool
    - Dispose SQLAlchemy engine
    """
    settings = get_settings()

    logger.info("Context-OS starting up (version=%s)", settings.app_version)

    # 1. Configure Langfuse env vars before tracer init
    configure_langfuse_env()

    # 2. Initialize OTEL tracer with Langfuse span processor
    init_tracer(settings.app_version)
    instrument_app(app)

    # 3. Initialize SQLAlchemy engine + pgvector codec
    await init_db()
    logger.info("Database engine initialized")

    # 4. Create AGE asyncpg pool
    pool = await create_age_pool()
    logger.info("AGE graph pool initialized")

    # 5. Initialize AGE graph
    await init_graph(pool)
    logger.info("AGE graph 'context_os' ready")

    logger.info("Context-OS startup complete")

    yield

    # Shutdown
    logger.info("Context-OS shutting down")
    await close_age_pool()
    await close_db()
    logger.info("Context-OS shutdown complete")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI app with all routers and middleware.
    """
    app = FastAPI(
        title="Context-OS API",
        description="AI-native operational intelligence platform — Phase 1 Foundation",
        version="0.1.0",
        lifespan=lifespan,
    )

    # ── Error handlers ────────────────────────────────────────────────────────

    @app.exception_handler(ContextOSError)
    async def context_os_error_handler(
        request: Request,
        exc: ContextOSError,
    ) -> JSONResponse:
        """Map ContextOSError subclasses to HTTP responses."""
        if isinstance(exc, AuthError):
            status_code = 401
        elif isinstance(exc, ValidationError):
            status_code = 400
        elif isinstance(exc, TenantIsolationError):
            status_code = 401
        else:
            status_code = 500
        return JSONResponse(
            status_code=status_code,
            content=exc.to_dict(),
        )

    # ── Routers ───────────────────────────────────────────────────────────────

    from context_os.api.admin import router as admin_router
    from context_os.api.graph import router as graph_router
    from context_os.api.ingest import router as ingest_router
    from context_os.api.vector import router as vector_router

    app.include_router(ingest_router, prefix="/ingest", tags=["Ingest"])
    app.include_router(graph_router, prefix="/graph", tags=["Graph"])
    app.include_router(vector_router, prefix="/vector", tags=["Vector"])
    app.include_router(admin_router, prefix="/admin", tags=["Admin"])

    @app.get("/health")
    async def health_check() -> dict[str, str]:
        """Health check endpoint (no auth required)."""
        return {"status": "ok", "version": "0.1.0"}

    return app


# Module-level app instance for uvicorn
app = create_app()
