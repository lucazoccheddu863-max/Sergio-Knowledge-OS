"""RateLimitPort — Infrastructure Port for M4.11 — Security & Auth.

Abstract interface for rate limiting.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class RateLimitStatus:
    """Rate limit check result."""
    allowed: bool
    remaining: int
    reset_after_seconds: float
    limit: int


class RateLimitPort(ABC):
    """Abstract port for rate limiting.

    Tracks request counts per client and decides whether a request
    is within the allowed quota.
    """

    @abstractmethod
    def check(self, client_id: str, resource: str) -> RateLimitStatus:
        """Check if the client is within rate limit for the resource.

        Args:
            client_id: Unique client identifier (e.g., API key, IP).
            resource: Resource being accessed.

        Returns:
            RateLimitStatus with allowance decision and quota info.
        """
        pass

    @abstractmethod
    def health(self) -> bool:
        """Check if the rate limiter is operational."""
        pass


class RateLimitExceededError(Exception):
    """Raised when a rate limit is exceeded."""
    pass
