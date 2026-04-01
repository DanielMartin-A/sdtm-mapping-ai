"""Structured logging configuration.

Fixes applied:
- H5: Accepts optional level override (used by --verbose flag)
"""

from __future__ import annotations

import logging

import structlog

from sdtm_mapping_ai.config import get_settings


def configure_logging(level: str | None = None) -> None:
    """Configure structlog for the application.

    Args:
        level: Optional override for log level (e.g., "DEBUG" from --verbose).
    """
    settings = get_settings()
    effective_level = level or settings.log_level

    processors: list = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    if settings.log_format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    numeric_level = getattr(logging, effective_level.upper(), logging.INFO)

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(numeric_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
    )
