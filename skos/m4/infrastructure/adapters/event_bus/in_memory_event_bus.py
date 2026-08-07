"""In-memory implementation of the Event Bus Port."""
from __future__ import annotations

import threading
import uuid
from collections import defaultdict
from typing import Any

from skos.m4.infrastructure.ports.event_bus_port import DomainEvent, EventBusPort, EventHandler, Subscription


class InMemoryEventBus(EventBusPort):
    def __init__(self) -> None:
        self._subscriptions: dict[str, list[Subscription]] = defaultdict(list)
        self._lock = threading.RLock()
        self._delivery_tags: dict[str, DomainEvent] = {}

    def publish(self, event: DomainEvent, topic: str) -> None:
        delivery_tag = str(uuid.uuid4())
        self._delivery_tags[delivery_tag] = event
        with self._lock:
            handlers = [sub.handler for sub in self._subscriptions.get(topic, []) if sub.active]
        for handler in handlers:
            try:
                handler.handler(event)
                self.ack(delivery_tag)
            except Exception:
                self.nack(delivery_tag, requeue=False)

    def subscribe(self, topic: str, handler: Any, group: str = "default") -> Subscription:
        event_handler = EventHandler(handler=handler, group=group)
        subscription = Subscription(topic=topic, handler=event_handler)
        with self._lock:
            self._subscriptions[topic].append(subscription)
        return subscription

    def ack(self, delivery_tag: str) -> None:
        self._delivery_tags.pop(delivery_tag, None)

    def nack(self, delivery_tag: str, requeue: bool = False) -> None:
        if not requeue:
            self._delivery_tags.pop(delivery_tag, None)

    def subscriber_count(self, topic: str) -> int:
        with self._lock:
            return sum(1 for sub in self._subscriptions.get(topic, []) if sub.active)
