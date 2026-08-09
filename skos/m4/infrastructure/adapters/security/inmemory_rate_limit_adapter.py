"""InMemoryRateLimitAdapter — Infrastructure Adapter for M4.11.

Sliding-window rate limiter backed by in-memory dictionaries.
"""
from __future__ import annotations

import time
from collections import deque
from typing import Any

from skos.m4.infrastructure.ports.rate_limit_port import (
    RateLimitPort,
    RateLimitStatus,
    RateLimitExceededError,
)


class InMemoryRateLimitAdapter(RateLimitPort):
    """In-memory sliding-window rate limiter.

    Tracks per-client, per-resource request timestamps in deques.
    Automatically evicts expired entries on each check.
    """

    def __init__(
        self,
        default_limit: int = 60,
        default_window_seconds: float = 60.0,
        overrides: dict[str, dict[str, Any]] | None = None,
    ) -> None:
        """Initialize rate limiter.

        Args:
            default_limit: Max requests per window.
            default_window_seconds: Window duration in seconds.
            overrides: Per-resource overrides, e.g. {"/api/v1/query": {"limit": 100}}.
        """
        self._default_limit = default_limit
        self._default_window = default_window_seconds
        self._overrides = dict(overrides or {})
        self._windows: dict[tuple[str, str], deque[float]] = {}

    def _get_limit(self, resource: str) -> tuple[int, float]:
        override = self._overrides.get(resource, {})
        return (
            override.get("limit", self._default_limit),
            override.get("window_seconds", self._default_window),
        )

    def check(self, client_id: str, resource: str) -> RateLimitStatus:
        now = time.monotonic()
        key = (client_id, resource)
        limit, window = self._get_limit(resource)
        window_deque = self._windows.setdefault(key, deque())

        # Evict expired timestamps
        cutoff = now - window
        while window_deque and window_deque[0] < cutoff:
            window_deque.popleft()

        remaining = limit - len(window_deque)
        if remaining > 0:
            window_deque.append(now)
            return RateLimitStatus(
                allowed=True,
                remaining=remaining - 1,
                reset_after_seconds=window,
                limit=limit,
            )

        reset_after = (window_deque[0] + window) - now if window_deque else 0.0
        return RateLimitStatus(
            allowed=False,
            remaining=0,
            reset_after_seconds=max(0.0, reset_after),
            limit=limit,
        )

    def health(self) -> bool:
        return True
