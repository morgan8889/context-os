"""Langfuse integration helpers.

Langfuse v4 is OTEL-native. The primary integration is via OTLPSpanExporter
pointed at the Langfuse OTLP endpoint, configured in observability/tracer.py.

This module provides convenience helpers for Langfuse-specific operations
that may be needed beyond the OTEL span exporter.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)


def configure_langfuse_env() -> None:
    """Set Langfuse environment variables from application settings.

    Langfuse SDK v3 reads LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, and
    LANGFUSE_HOST from environment variables. This function ensures they
    are set from our settings object before the SDK initializes.

    Should be called before init_tracer().
    """
    try:
        from context_os.config import get_settings

        settings = get_settings()
        os.environ.setdefault("LANGFUSE_PUBLIC_KEY", settings.langfuse_public_key)
        os.environ.setdefault("LANGFUSE_SECRET_KEY", settings.langfuse_secret_key)
        os.environ.setdefault("LANGFUSE_HOST", settings.langfuse_host)
        logger.debug("Langfuse environment variables configured")
    except Exception as e:
        logger.warning("Failed to configure Langfuse env vars: %s", e)
