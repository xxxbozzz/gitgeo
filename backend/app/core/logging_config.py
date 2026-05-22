"""Structured logging configuration for the backend API."""

import logging
import sys
from datetime import datetime, timezone


LOG_FORMAT_JSON = "%(message)s"
LOG_FORMAT_CONSOLE = "%(asctime)s [%(name)s] %(levelname)s  %(message)s"


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        import json
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[0]:
            import traceback
            payload["exception"] = traceback.format_exception(*record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)


def setup_logging(*, json_format: bool = False) -> None:
    root = logging.getLogger("geo_backend")
    root.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    if json_format:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(LOG_FORMAT_CONSOLE, datefmt="%H:%M:%S")
        )
    root.handlers.clear()
    root.addHandler(handler)
    root.propagate = False
