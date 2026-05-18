"""OpenTelemetry TracerProvider setup with Langfuse OTLP export.

Langfuse v3+ is OTEL-native. For Langfuse v4, we use the OTLP HTTP exporter
pointed at the Langfuse OTLP endpoint. FastAPIInstrumentor auto-instruments
all routes.

Langfuse v4 integration: export spans via OTLPSpanExporter to
{LANGFUSE_HOST}/api/public/otel with public/secret key as Basic auth.
"""

from __future__ import annotations

import base64
import logging
import os

from opentelemetry import trace
from opentelemetry.sdk.resources import SERVICE_NAME, SERVICE_VERSION, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

logger = logging.getLogger(__name__)

_tracer_provider: TracerProvider | None = None


def init_tracer(app_version: str = "0.1.0") -> TracerProvider:
    """Initialize the global TracerProvider with Langfuse OTLP export.

    Sets up:
    - TracerProvider with SERVICE_NAME="context-os" resource
    - OTLPSpanExporter to Langfuse OTLP endpoint (Langfuse v4 integration)
    - Global tracer provider via trace.set_tracer_provider()

    Args:
        app_version: Application semver for OTEL resource attributes.

    Returns:
        The initialized TracerProvider.
    """
    global _tracer_provider

    resource = Resource(
        attributes={
            SERVICE_NAME: "context-os",
            SERVICE_VERSION: app_version,
        }
    )

    provider = TracerProvider(resource=resource)

    # Add Langfuse OTLP span exporter
    # Langfuse v4 uses OTLPSpanExporter with Basic auth (public:secret keys)
    try:
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter,
        )

        langfuse_host = os.environ.get("LANGFUSE_HOST", "http://localhost:3000")
        public_key = os.environ.get("LANGFUSE_PUBLIC_KEY", "")
        secret_key = os.environ.get("LANGFUSE_SECRET_KEY", "")

        if public_key and secret_key:
            # Basic auth: base64(public_key:secret_key)
            auth_str = f"{public_key}:{secret_key}"
            auth_b64 = base64.b64encode(auth_str.encode()).decode()

            exporter = OTLPSpanExporter(
                endpoint=f"{langfuse_host}/api/public/otel/v1/traces",
                headers={"Authorization": f"Basic {auth_b64}"},
            )
            provider.add_span_processor(BatchSpanProcessor(exporter))
            logger.info(
                "Langfuse OTLP span exporter registered: %s/api/public/otel",
                langfuse_host,
            )
        else:
            logger.warning(
                "LANGFUSE_PUBLIC_KEY or LANGFUSE_SECRET_KEY not set; "
                "traces will not be exported to Langfuse"
            )
    except Exception as e:
        logger.warning("Failed to register Langfuse OTLP exporter: %s", e)

    trace.set_tracer_provider(provider)
    _tracer_provider = provider
    logger.info("OTEL TracerProvider initialized (version=%s)", app_version)
    return provider


def get_tracer(name: str) -> trace.Tracer:
    """Return a named tracer from the global provider.

    Args:
        name: Tracer name (typically module path, e.g. "context_os.api.ingest").

    Returns:
        Tracer instance for creating spans.

    Raises:
        RuntimeError: If init_tracer() has not been called.
    """
    if _tracer_provider is None:
        raise RuntimeError("Tracer not initialized; call init_tracer() first")
    return _tracer_provider.get_tracer(name)


def instrument_app(app: object) -> None:
    """Instrument a FastAPI application with OTEL auto-instrumentation.

    Wraps all FastAPI routes with OTEL spans automatically.

    Args:
        app: FastAPI application instance.
    """
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        provider = _tracer_provider or trace.get_tracer_provider()
        FastAPIInstrumentor.instrument_app(  # type: ignore[attr-defined]
            app,  # type: ignore[arg-type]
            tracer_provider=provider,
        )
        logger.info("FastAPI OTEL auto-instrumentation enabled")
    except Exception as e:
        logger.warning("Failed to instrument FastAPI app: %s", e)


def get_current_trace_id() -> str | None:
    """Return the current OTEL trace ID as a hex string, or None if no active span.

    Returns:
        Hex trace ID string (32 chars) or None.
    """
    span = trace.get_current_span()
    ctx = span.get_span_context()
    if ctx and ctx.trace_id:
        return format(ctx.trace_id, "032x")
    return None
