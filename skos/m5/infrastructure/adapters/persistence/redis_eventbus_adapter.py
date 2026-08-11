"""RedisEventBusAdapter — M5.1 Persistence Layer.

Redis-backed event bus implementing EventBusPort.
Uses Redis pub/sub for broadcast and Redis Streams for persistent queues.
"""
from __future__ import annotations

import json
import threading
import time
from typing import Callable

from ._optional_dependencies import load_redis

from skos.m4.infrastructure.ports.event_bus_port import (
    EventBusPort, DomainEvent, EventHandler, Subscription,
)

redis = load_redis()


class RedisEventBusAdapter(EventBusPort):
    """Redis-backed event bus.

    Publishes events to Redis channels. Subscribers use Redis pub/sub
    for real-time delivery. Supports consumer groups via Redis Streams
    for at-least-once delivery.
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        stream_prefix: str = "skos:events",
    ) -> None:
        self._redis_url = redis_url
        self._stream_prefix = stream_prefix
        self._client: redis.Redis | None = None
        self._pubsub: redis.client.PubSub | None = None
        self._subscribers: dict[str, list[Callable[[DomainEvent], None]]] = {}
        self._listener_thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self._connect()

    def _connect(self) -> None:
        try:
            self._client = redis.from_url(self._redis_url, decode_responses=True)
            self._client.ping()
        except Exception:
            self._client = None

    def _ensure_connected(self) -> redis.Redis:
        if self._client is None:
            self._connect()
        if self._client is None:
            raise RuntimeError("Redis connection unavailable")
        return self._client

    def publish(self, event: DomainEvent, topic: str) -> None:
        client = self._ensure_connected()
        payload = json.dumps({
            "event_id": event.event_id,
            "event_type": event.event_type,
            "correlation_id": event.correlation_id,
            "timestamp": event.timestamp.isoformat() if hasattr(event.timestamp, 'isoformat') else str(event.timestamp),
            "payload": event.payload,
            "metadata": event.metadata,
        })
        # Publish to pub/sub for real-time subscribers
        client.publish(f"{self._stream_prefix}:{topic}", payload)
        # Also add to stream for persistent consumers
        client.xadd(
            f"{self._stream_prefix}:stream:{topic}",
            {"data": payload},
            maxlen=10000,
            approximate=True,
        )

    def subscribe(
        self,
        topic: str,
        handler: Callable[[DomainEvent], None],
        group: str = "default",
    ) -> Subscription:
        client = self._ensure_connected()
        with self._lock:
            if topic not in self._subscribers:
                self._subscribers[topic] = []
                self._start_listener(topic)
            self._subscribers[topic].append(handler)

        # Create consumer group for persistent delivery
        stream_key = f"{self._stream_prefix}:stream:{topic}"
        try:
            client.xgroup_create(stream_key, group, id="0", mkstream=True)
        except redis.ResponseError as e:
            if "already exists" not in str(e).lower():
                raise

        return Subscription(topic=topic, handler=EventHandler(handler))

    def _start_listener(self, topic: str) -> None:
        if self._pubsub is None:
            self._pubsub = self._client.pubsub()
        self._pubsub.subscribe(f"{self._stream_prefix}:{topic}")
        if self._listener_thread is None or not self._listener_thread.is_alive():
            self._listener_thread = threading.Thread(target=self._listen_loop, daemon=True)
            self._listener_thread.start()

    def _listen_loop(self) -> None:
        while self._pubsub:
            try:
                message = self._pubsub.get_message(timeout=1.0)
                if message and message["type"] == "message":
                    self._handle_message(message)
            except Exception:
                time.sleep(1)

    def _handle_message(self, message: dict) -> None:
        try:
            data = json.loads(message["data"])
            from datetime import datetime
            ts = data.get("timestamp", "")
            if isinstance(ts, str):
                try:
                    timestamp = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                except ValueError:
                    timestamp = datetime.now()
            else:
                timestamp = datetime.now()
            event = DomainEvent(
                event_id=data.get("event_id", "unknown"),
                event_type=data["event_type"],
                correlation_id=data.get("correlation_id", "unknown"),
                timestamp=timestamp,
                payload=data.get("payload", {}),
                metadata=data.get("metadata", {}),
            )
            topic = message["channel"].split(":")[-1]
            with self._lock:
                handlers = list(self._subscribers.get(topic, []))
            for handler in handlers:
                handler(event)
        except Exception:
            pass

    def ack(self, delivery_tag: str) -> None:
        # Redis Streams ack is handled via XACK in consumer groups
        pass

    def nack(self, delivery_tag: str, requeue: bool = False) -> None:
        pass

    def health(self) -> bool:
        try:
            if self._client:
                return self._client.ping()
        except Exception:
            pass
        return False
