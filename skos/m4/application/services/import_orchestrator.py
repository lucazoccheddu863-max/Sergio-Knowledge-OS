"""Application service for coordinating import workflows.

Emits domain events to decouple import phases from downstream consumers
(e.g. indexing, embedding generation, duplicate detection).
"""
from __future__ import annotations

from skos.m4.infrastructure.ports.event_bus_port import DomainEvent, EventBusPort


class ImportOrchestrator:
    """Orchestrates the import pipeline using domain events."""

    def __init__(self, event_bus: EventBusPort) -> None:
        self._event_bus = event_bus

    def start_import(self, source_id: int, source_name: str) -> None:
        """Emit an import started event."""
        event = DomainEvent(
            event_id=f"import-started-{source_id}",
            event_type="import.started",
            correlation_id=f"corr-{source_id}",
            payload={"source_id": source_id, "source_name": source_name},
        )
        self._event_bus.publish(event, topic="import.events")

    def complete_import(self, source_id: int, files_processed: int) -> None:
        """Emit an import completed event."""
        event = DomainEvent(
            event_id=f"import-completed-{source_id}",
            event_type="import.completed",
            correlation_id=f"corr-{source_id}",
            payload={"source_id": source_id, "files_processed": files_processed},
        )
        self._event_bus.publish(event, topic="import.events")

    def import_failed(self, source_id: int, error: str) -> None:
        """Emit an import failed event."""
        event = DomainEvent(
            event_id=f"import-failed-{source_id}",
            event_type="import.failed",
            correlation_id=f"corr-{source_id}",
            payload={"source_id": source_id, "error": error},
        )
        self._event_bus.publish(event, topic="import.events")
