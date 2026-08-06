"""Value objects for the M4 domain."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ConfigScope:
    """Represents a configuration scope in the hierarchy.

    Scopes are ordered from most general to most specific:
    system < tenant < workspace < project < user
    """
    system: bool = True
    tenant_id: str | None = None
    workspace_id: str | None = None
    project_id: str | None = None
    user_id: str | None = None

    def to_tuple(self) -> tuple[bool, str | None, str | None, str | None, str | None]:
        return (self.system, self.tenant_id, self.workspace_id, self.project_id, self.user_id)

    def __lt__(self, other: ConfigScope) -> bool:
        return self.to_tuple() < other.to_tuple()

    def __le__(self, other: ConfigScope) -> bool:
        return self.to_tuple() <= other.to_tuple()


@dataclass(frozen=True)
class ConfigPath:
    """A dotted path to a configuration value."""
    path: str

    def parts(self) -> list[str]:
        return self.path.split(".")

    def parent(self) -> ConfigPath:
        parts = self.parts()
        if len(parts) <= 1:
            return ConfigPath("")
        return ConfigPath(".".join(parts[:-1]))

    def __str__(self) -> str:
        return self.path


@dataclass(frozen=True)
class SecretRef:
    """Reference to a secret stored in a Secret Manager."""
    key: str
    namespace: str = "default"
