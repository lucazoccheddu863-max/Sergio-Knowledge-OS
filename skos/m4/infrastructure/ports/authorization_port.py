"""AuthorizationPort — Infrastructure Port for M4.11 — Security & Auth.

Abstract interface for authorization / RBAC.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from skos.m4.infrastructure.ports.auth_port import SecurityContext


class AuthorizationPort(ABC):
    """Abstract port for authorization.

    Decides whether a SecurityContext is allowed to perform an action
    on a given resource.
    """

    @abstractmethod
    def authorize(
        self,
        context: SecurityContext,
        action: str,
        resource: str,
    ) -> bool:
        """Check if the principal is authorized.

        Args:
            context: SecurityContext from authentication.
            action: Action to perform (e.g., "read", "write", "admin").
            resource: Resource identifier (e.g., "/api/v1/query").

        Returns:
            True if authorized, False otherwise.
        """
        pass

    @abstractmethod
    def health(self) -> bool:
        """Check if the authorization subsystem is operational."""
        pass


class AuthorizationError(Exception):
    """Base error for authorization operations."""
    pass
