# backend/app/core/logging.py
import logging
import sys

import structlog


def setup_logging(log_level: str = "info") -> None:
    """Configure structured logging for the application.

    Args:
        log_level: Logging level string (debug, info, warning, error).
    """
    log_level_int = getattr(logging, log_level.upper(), logging.INFO)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer() if sys.stderr.isatty() else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level_int),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = __name__):
    """Return a structured logger instance.

    Args:
        name: Logger name, typically the calling module's __name__.

    Returns:
        A structlog BoundLogger instance.
    """
    return structlog.get_logger(name)
