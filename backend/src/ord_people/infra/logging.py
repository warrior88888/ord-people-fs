from __future__ import annotations

import logging
import logging.config
import os
from contextvars import ContextVar
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ord_people.config.log import LoggingConfig

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")
user_id_var: ContextVar[str] = ContextVar("user_id", default="-")


def _file_handler_ready(file_path: str) -> bool:
    """Make file logging best-effort: never crash app boot because of it.

    Tries to mkdir the parent and touch the file. On any OSError logs a warning
    to stderr and returns False so the caller skips the file handler entirely.
    """
    try:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8"):
            pass
    except OSError as exc:
        os.write(2, f"logging: file handler disabled ({file_path}): {exc}\n".encode())
        return False
    return True


class ContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id"):
            record.request_id = request_id_var.get()
        if not hasattr(record, "user_id"):
            record.user_id = user_id_var.get()
        return True


def setup_logging(config: LoggingConfig) -> None:
    handlers: dict[str, dict] = {
        "console": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "formatter": "default",
            "filters": ["context"],
        },
    }

    root_handlers = ["console"]

    if config.to_file and _file_handler_ready(config.file_path):
        handlers["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": config.file_path,
            "maxBytes": config.max_size_bytes,
            "backupCount": config.file_backup_count,
            "formatter": "default",
            "filters": ["context"],
            "encoding": "utf-8",
            # delay=True: don't open the file at handler construction —
            # only on first emit. Keeps the app bootable even if the
            # mount permission is fixed lazily.
            "delay": True,
        }
        root_handlers.append("file")

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "filters": {
                "context": {"()": ContextFilter},
            },
            "formatters": {
                "default": {
                    "format": config.format,
                },
            },
            "handlers": handlers,
            "root": {
                "level": config.level,
                "handlers": root_handlers,
            },
            "loggers": {
                "sqlalchemy.engine": {"level": config.db_level},
                "sqlalchemy.pool": {"level": config.db_level},
                "uvicorn.access": {
                    "level": "INFO" if config.access_log else "WARNING",
                },
                "uvicorn.error": {"level": config.level},
                "botocore": {"level": "WARNING"},
                "aiobotocore": {"level": "WARNING"},
                "urllib3": {"level": "WARNING"},
                "asyncio": {"level": "WARNING"},
            },
        }
    )
