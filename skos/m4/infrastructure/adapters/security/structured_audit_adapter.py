"""StructuredAuditAdapter — Infrastructure Adapter for M4.11.

JSON-structured audit logging to configurable output stream.
"""
from __future__ import annotations

import json
import sys
from typing import Any, TextIO

from skos.m4.infrastructure.ports.audit_port import AuditPort, AuditEvent


class StructuredAuditAdapter(AuditPort):
    """Structured JSON audit logger.

    Writes one JSON line per audit event to the configured output.
    """

    def __init__(
        self,
        service_name: str = "skos",
        output: TextIO | None = None,
    ) -> None:
        self._service = service_name
        self._output = output or sys.stdout

    def record(self, event: AuditEvent) -> None:
        entry = {
            "service": self._service,
            "timestamp": event.timestamp,
            "event_type": event.event_type,
            "principal": event.principal,
            "action": event.action,
            "resource": event.resource,
            "status": event.status,
            "details": event.details,
        }
        self._output.write(json.dumps(entry) + "\n")
        self._output.flush()

    def health(self) -> bool:
        return not self._output.closed
