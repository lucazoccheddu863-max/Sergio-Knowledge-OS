"""TracingPort — Infrastructure Port for M4.10."""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any

class TracingPort(ABC):
    @abstractmethod
    def start_span(self, name: str, context: dict[str, Any] | None = None) -> Any: ...
    @abstractmethod
    def end_span(self, span: Any) -> None: ...
    @abstractmethod
    def record_exception(self, span: Any, exception: Exception) -> None: ...
    @abstractmethod
    def health(self) -> bool: ...
