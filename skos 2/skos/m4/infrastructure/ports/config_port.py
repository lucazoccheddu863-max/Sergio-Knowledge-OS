"""Configuration Port — abstract interface for configuration management."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable

from skos.m4.domain.value_objects import ConfigPath, ConfigScope


class ConfigurationPort(ABC):
    """Abstract port for hierarchical, hot-reloadable configuration."""

    @abstractmethod
    def get(
        self,
        path: str | ConfigPath,
        scope: ConfigScope | None = None,
        default: Any = None,
    ) -> Any:
        """Get a configuration value at the given path and scope."""

    @abstractmethod
    def get_with_fallback(
        self,
        path: str | ConfigPath,
        scopes: list[ConfigScope],
        default: Any = None,
    ) -> Any:
        """Get a configuration value trying multiple scopes in order."""

    @abstractmethod
    def set(
        self,
        path: str | ConfigPath,
        value: Any,
        scope: ConfigScope | None = None,
    ) -> None:
        """Set a configuration value at the given path and scope."""

    @abstractmethod
    def subscribe(
        self,
        path: str | ConfigPath,
        callback: Callable[[Any], None],
    ) -> "ConfigSubscription":
        """Subscribe to changes at a configuration path."""

    @abstractmethod
    def reload(self, scope: ConfigScope | None = None) -> None:
        """Reload configuration from external sources for the given scope."""

    @abstractmethod
    def dump(self, scope: ConfigScope | None = None) -> dict[str, Any]:
        """Dump the full configuration for a scope as a dictionary."""


class ConfigSubscription:
    """Handle for a configuration subscription."""

    def __init__(self, path: str, callback: Callable[[Any], None]) -> None:
        self.path = path
        self.callback = callback
        self.active = True

    def unsubscribe(self) -> None:
        """Deactivate this subscription."""
        self.active = False
