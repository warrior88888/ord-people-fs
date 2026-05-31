from __future__ import annotations

import logging
import logging.config
from contextvars import ContextVar
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ord_people.config.log import LoggingConfig

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")
user_id_var: ContextVar[str] = ContextVar("user_id", default="-")


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

    if config.to_file:
        handlers["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": config.file_path,
            "maxBytes": config.max_size_bytes,
            "backupCount": config.file_backup_count,
            "formatter": "default",
            "filters": ["context"],
            "encoding": "utf-8",
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
