"""StructuredLoggingAdapter — Infrastructure Adapter for M4.10."""
from __future__ import annotations
import json
import sys
from datetime import datetime, timezone
from typing import Any
from skos.m4.infrastructure.ports.logging_port import LoggingPort

class StructuredLoggingAdapter(LoggingPort):
    def __init__(self, service_name: str = "skos", output: Any = sys.stderr) -> None:
        self._service_name = service_name
        self._output = output

    def _log(self, level: str, message: str, **kwargs: Any) -> None:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": self._service_name,
            "level": level,
            "message": message,
        }
        entry.update(kwargs)
        self._output.write(json.dumps(entry) + "\n")

    def debug(self, message: str, **kwargs: Any) -> None:
        self._log("DEBUG", message, **kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        self._log("INFO", message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        self._log("WARNING", message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        self._log("ERROR", message, **kwargs)

    def health(self) -> bool:
        return True
