"""Structured logging configuration using structlog.

Every log line includes run_id, agent_id, and phase for filterability.
Usage:
    from src.logging import get_logger
    log = get_logger()
    log.info("agent_complete", agent_id="quant_analyst", run_id="abc123")
"""

from __future__ import annotations

import logging
import sys

import structlog

from src.config import get_config


def setup_logging() -> None:
    """Configure structlog with JSON output for production or console for dev."""
    config = get_config()
    level = getattr(logging, config.log_level.upper(), logging.INFO)

    processors: list = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if config.log_level == "DEBUG":
        processors.append(structlog.dev.ConsoleRenderer())
    else:
        processors.append(structlog.processors.JSONRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(format="%(message)s", level=level, stream=sys.stderr)


def get_logger(**initial_bindings: object) -> structlog.stdlib.BoundLogger:
    """Get a bound logger with optional initial context."""
    return structlog.get_logger(**initial_bindings)
