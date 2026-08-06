"""Secret Manager Port — abstract interface for secret storage."""
from __future__ import annotations

from abc import ABC, abstractmethod

from skos.m4.domain.value_objects import SecretRef


class SecretManagerPort(ABC):
    """Abstract port for secure secret storage and retrieval."""

    @abstractmethod
    def get(self, ref: SecretRef) -> str:
        """Retrieve a secret by reference."""

    @abstractmethod
    def set(self, ref: SecretRef, value: str) -> None:
        """Store or update a secret."""

    @abstractmethod
    def delete(self, ref: SecretRef) -> None:
        """Delete a secret."""

    @abstractmethod
    def exists(self, ref: SecretRef) -> bool:
        """Check if a secret exists."""

    @abstractmethod
    def list_keys(self, namespace: str = "default") -> list[str]:
        """List all secret keys in a namespace."""


class SecretNotFoundError(Exception):
    """Raised when a requested secret is not found."""


class SecretAccessError(Exception):
    """Raised when secret access is denied."""
