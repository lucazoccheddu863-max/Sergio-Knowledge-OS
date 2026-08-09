"""AuthPort — Infrastructure Port for M4.11 — Security & Auth.

Abstract interface for authentication mechanisms.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class SecurityContext:
    """Immutable security context passed through the request lifecycle."""
    authenticated: bool = False
    principal: str | None = None
    roles: list[str] = field(default_factory=list)
    api_key_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class AuthPort(ABC):
    """Abstract port for authentication.

    Validates credentials and returns a SecurityContext.
    """

    @abstractmethod
    def authenticate(self, credentials: str | None) -> SecurityContext:
        """Authenticate the given credentials.

        Args:
            credentials: Raw credential string (e.g., API key, Bearer token).

        Returns:
            SecurityContext with authentication result.
        """
        pass

    @abstractmethod
    def health(self) -> bool:
        """Check if the auth subsystem is operational."""
        pass


class AuthError(Exception):
    """Base error for authentication operations."""
    pass
