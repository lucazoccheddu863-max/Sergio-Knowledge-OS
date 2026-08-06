"""Tests for the Event Bus adapter and application services."""
from __future__ import annotations

import pytest

from skos.m4.infrastructure.adapters.event_bus.in_memory_event_bus import (
    InMemoryEventBus,
)
from skos.m4.infrastructure.ports.event_bus_port import DomainEvent
from skos.m4.application.services.import_orchestrator import ImportOrchestrator


class TestInMemoryEventBus:
    def test_publish_and_subscribe(self) -> None:
        bus = InMemoryEventBus()
        received: list[DomainEvent] = []

        def handler(event: DomainEvent) -> None:
            received.append(event)

        sub = bus.subscribe("test.topic", handler)
        event = DomainEvent(
            event_id="evt-1",
            event_type="test.event",
            correlation_id="corr-1",
            payload={"msg": "hello"},
        )
        bus.publish(event, "test.topic")

        assert len(received) == 1
        assert received[0].event_type == "test.event"
        assert received[0].payload["msg"] == "hello"

    def test_unsubscribe(self) -> None:
        bus = InMemoryEventBus()
        received: list[DomainEvent] = []

        def handler(event: DomainEvent) -> None:
            received.append(event)

        sub = bus.subscribe("test.topic", handler)
        sub.unsubscribe()

        event = DomainEvent(
            event_id="evt-2",
            event_type="test.event",
            correlation_id="corr-2",
        )
        bus.publish(event, "test.topic")

        assert len(received) == 0

    def test_no_subscribers_no_error(self) -> None:
        bus = InMemoryEventBus()
        event = DomainEvent(
            event_id="evt-3",
            event_type="test.event",
            correlation_id="corr-3",
        )
        bus.publish(event, "empty.topic")  # Should not raise

    def test_multiple_subscribers(self) -> None:
        bus = InMemoryEventBus()
        received_a: list[DomainEvent] = []
        received_b: list[DomainEvent] = []

        bus.subscribe("multi.topic", lambda e: received_a.append(e))
        bus.subscribe("multi.topic", lambda e: received_b.append(e))

        event = DomainEvent(
            event_id="evt-4",
            event_type="test.event",
            correlation_id="corr-4",
        )
        bus.publish(event, "multi.topic")

        assert len(received_a) == 1
        assert len(received_b) == 1

    def test_subscriber_count(self) -> None:
        bus = InMemoryEventBus()
        assert bus.subscriber_count("count.topic") == 0
        sub1 = bus.subscribe("count.topic", lambda e: None)
        assert bus.subscriber_count("count.topic") == 1
        sub2 = bus.subscribe("count.topic", lambda e: None)
        assert bus.subscriber_count("count.topic") == 2
        sub1.unsubscribe()
        assert bus.subscriber_count("count.topic") == 1

    def test_handler_exception_does_not_crash_bus(self) -> None:
        bus = InMemoryEventBus()
        received: list[DomainEvent] = []

        def bad_handler(event: DomainEvent) -> None:
            raise RuntimeError("boom")

        def good_handler(event: DomainEvent) -> None:
            received.append(event)

        bus.subscribe("fault.topic", bad_handler)
        bus.subscribe("fault.topic", good_handler)

        event = DomainEvent(
            event_id="evt-5",
            event_type="test.event",
            correlation_id="corr-5",
        )
        bus.publish(event, "fault.topic")

        assert len(received) == 1


class TestImportOrchestrator:
    def test_start_import_emits_event(self) -> None:
        bus = InMemoryEventBus()
        captured: list[DomainEvent] = []

        bus.subscribe("import.events", lambda e: captured.append(e))

        orchestrator = ImportOrchestrator(bus)
        orchestrator.start_import(source_id=42, source_name="test-source")

        assert len(captured) == 1
        assert captured[0].event_type == "import.started"
        assert captured[0].payload["source_id"] == 42
        assert captured[0].payload["source_name"] == "test-source"

    def test_complete_import_emits_event(self) -> None:
        bus = InMemoryEventBus()
        captured: list[DomainEvent] = []

        bus.subscribe("import.events", lambda e: captured.append(e))

        orchestrator = ImportOrchestrator(bus)
        orchestrator.complete_import(source_id=42, files_processed=100)

        assert len(captured) == 1
        assert captured[0].event_type == "import.completed"
        assert captured[0].payload["files_processed"] == 100

    def test_import_failed_emits_event(self) -> None:
        bus = InMemoryEventBus()
        captured: list[DomainEvent] = []

        bus.subscribe("import.events", lambda e: captured.append(e))

        orchestrator = ImportOrchestrator(bus)
        orchestrator.import_failed(source_id=42, error="disk full")

        assert len(captured) == 1
        assert captured[0].event_type == "import.failed"
        assert captured[0].payload["error"] == "disk full"
