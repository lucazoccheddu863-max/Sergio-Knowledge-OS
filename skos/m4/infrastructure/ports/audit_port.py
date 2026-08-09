"""AuditPort — Infrastructure Port for M4.11 — Security & Auth.

Abstract interface for security audit logging.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any
from datetime import datetime


@dataclass
class AuditEvent:
    """Immutable audit event record."""
    timestamp: str
    event_type: str
    principal: str | None
    action: str
    resource: str
    status: str
    details: dict[str, Any] = field(default_factory=dict)


class AuditPort(ABC):
    """Abstract port for audit logging.

    Records security-relevant events for compliance and forensics.
    """

    @abstractmethod
    def record(self, event: AuditEvent) -> None:
        """Record an audit event.

        Args:
            event: AuditEvent to persist.
        """
        pass

    @abstractmethod
    def health(self) -> bool:
        """Check if the audit subsystem is operational."""
        pass
