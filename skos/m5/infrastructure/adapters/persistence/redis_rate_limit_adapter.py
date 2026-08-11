"""RedisRateLimitAdapter — M5.1 Persistence Layer.

Distributed sliding-window rate limiter backed by Redis.
"""
from __future__ import annotations

import time
from typing import Any

from ._optional_dependencies import load_redis

from skos.m4.infrastructure.ports.rate_limit_port import (
    RateLimitPort, RateLimitStatus, RateLimitExceededError,
)

redis = load_redis()


class RedisRateLimitAdapter(RateLimitPort):
    """Distributed sliding-window rate limiter using Redis sorted sets.

    Each window is a Redis sorted set where score = timestamp.
    ZREMRANGEBYSCORE evicts expired entries.
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        default_limit: int = 60,
        default_window_seconds: float = 60.0,
        overrides: dict[str, dict[str, Any]] | None = None,
    ) -> None:
        self._redis_url = redis_url
        self._default_limit = default_limit
        self._default_window = default_window_seconds
        self._overrides = dict(overrides or {})
        self._client: redis.Redis | None = None
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

    def _get_limit(self, resource: str) -> tuple[int, float]:
        override = self._overrides.get(resource, {})
        return (
            override.get("limit", self._default_limit),
            override.get("window_seconds", self._default_window),
        )

    def _key(self, client_id: str, resource: str) -> str:
        return f"skos:ratelimit:{client_id}:{resource}"

    def check(self, client_id: str, resource: str) -> RateLimitStatus:
        client = self._ensure_connected()
        now = time.time()
        key = self._key(client_id, resource)
        limit, window = self._get_limit(resource)

        pipe = client.pipeline()
        # Remove expired entries
        pipe.zremrangebyscore(key, 0, now - window)
        # Count current entries
        pipe.zcard(key)
        # Add current request
        pipe.zadd(key, {str(now): now})
        # Set expiry on the key
        pipe.expire(key, int(window) + 1)
        results = pipe.execute()

        current_count = results[1]  # zcard result before zadd
        # After zadd, count is current_count + 1
        remaining = limit - current_count - 1

        if remaining >= 0:
            return RateLimitStatus(
                allowed=True,
                remaining=remaining,
                reset_after_seconds=window,
                limit=limit,
            )

        # Rollback: remove the entry we just added
        client.zrem(key, str(now))
        reset_after = window
        return RateLimitStatus(
            allowed=False,
            remaining=0,
            reset_after_seconds=reset_after,
            limit=limit,
        )

    def health(self) -> bool:
        try:
            if self._client:
                return self._client.ping()
        except Exception:
            pass
        return False
