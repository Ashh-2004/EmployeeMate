import logging
import json
import time
from contextvars import ContextVar
from typing import Any, Dict

request_id_var: ContextVar[str] = ContextVar("request_id", default="")


class JSONFormatter(logging.Formatter):
    """Custom JSON log formatter including timestamp, level, logger, request_id, and message."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_var.get(""),
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Configures structured JSON logging for the application."""
    level = getattr(logging, log_level.upper(), logging.INFO)
    logger = logging.getLogger("employeemate")
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)

    logger.propagate = False
    return logger


logger = setup_logging()
