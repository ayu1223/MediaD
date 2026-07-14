from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from app.core.constants import LOG_BACKUP_COUNT, LOG_FILE_NAME, LOG_MAX_BYTES
from app.core.paths import get_log_dir

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_configured = False


def configure_logging(console_level: int = logging.WARNING, file_level: int = logging.DEBUG) -> None:
    """Configure the root logger with a rotating file handler and a console handler.

    Safe to call multiple times; only the first call takes effect.
    """
    global _configured
    if _configured:
        return

    root_logger = logging.getLogger()
    root_logger.setLevel(min(console_level, file_level))

    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)

    log_path = get_log_dir() / LOG_FILE_NAME
    file_handler = RotatingFileHandler(
        log_path, maxBytes=LOG_MAX_BYTES, backupCount=LOG_BACKUP_COUNT, encoding="utf-8"
    )
    file_handler.setLevel(file_level)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(formatter)

    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Return a module-scoped logger. Call configure_logging() once at startup first."""
    return logging.getLogger(name)
