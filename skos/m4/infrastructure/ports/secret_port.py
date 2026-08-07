"""Secret Manager Port — abstract interface for secret storage."""
from __future__ import annotations

from abc import ABC, abstractmethod

from skos.m4.domain.value_objects import SecretRef


class SecretManagerPort(ABC):
    @abstractmethod
    def get(self, ref: SecretRef) -> str:
        pass

    @abstractmethod
    def set(self, ref: SecretRef, value: str) -> None:
        pass

    @abstractmethod
    def delete(self, ref: SecretRef) -> None:
        pass

    @abstractmethod
    def exists(self, ref: SecretRef) -> bool:
        pass

    @abstractmethod
    def list_keys(self, namespace: str = "default") -> list[str]:
        pass


class SecretNotFoundError(Exception):
    pass


class SecretAccessError(Exception):
    pass
