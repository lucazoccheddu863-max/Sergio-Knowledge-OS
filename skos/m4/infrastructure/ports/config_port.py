"""Configuration Port — abstract interface for configuration management."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable

from skos.m4.domain.value_objects import ConfigPath, ConfigScope


class ConfigurationPort(ABC):
    @abstractmethod
    def get(self, path: str | ConfigPath, scope: ConfigScope | None = None, default: Any = None) -> Any:
        pass

    @abstractmethod
    def get_with_fallback(self, path: str | ConfigPath, scopes: list[ConfigScope], default: Any = None) -> Any:
        pass

    @abstractmethod
    def set(self, path: str | ConfigPath, value: Any, scope: ConfigScope | None = None) -> None:
        pass

    @abstractmethod
    def subscribe(self, path: str | ConfigPath, callback: Callable[[Any], None]) -> "ConfigSubscription":
        pass

    @abstractmethod
    def reload(self, scope: ConfigScope | None = None) -> None:
        pass

    @abstractmethod
    def dump(self, scope: ConfigScope | None = None) -> dict[str, Any]:
        pass


class ConfigSubscription:
    def __init__(self, path: str, callback: Callable[[Any], None]) -> None:
        self.path = path
        self.callback = callback
        self.active = True

    def unsubscribe(self) -> None:
        self.active = False
