"""Event Bus Port — abstract interface for event-driven communication."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable


@dataclass(frozen=True)
class DomainEvent:
    """Base class for all domain events."""
    event_id: str
    event_type: str
    correlation_id: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    payload: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EventHandler:
    """Wrapper for an event handler function."""
    handler: Callable[[DomainEvent], None]
    group: str = "default"
    event_types: list[str] | None = None


class Subscription:
    """Handle for an event subscription."""

    def __init__(self, topic: str, handler: EventHandler) -> None:
        self.topic = topic
        self.handler = handler
        self.active = True

    def unsubscribe(self) -> None:
        """Deactivate this subscription."""
        self.active = False


class EventBusPort(ABC):
    """Abstract port for publish/subscribe event communication."""

    @abstractmethod
    def publish(self, event: DomainEvent, topic: str) -> None:
        """Publish an event to a topic."""

    @abstractmethod
    def subscribe(
        self,
        topic: str,
        handler: Callable[[DomainEvent], None],
        group: str = "default",
    ) -> Subscription:
        """Subscribe to events on a topic."""

    @abstractmethod
    def ack(self, delivery_tag: str) -> None:
        """Acknowledge successful processing of a message."""

    @abstractmethod
    def nack(self, delivery_tag: str, requeue: bool = False) -> None:
        """Negative acknowledge — message processing failed."""
