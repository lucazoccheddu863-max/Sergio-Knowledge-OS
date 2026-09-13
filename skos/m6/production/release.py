"""Release status helpers for SKOS admin operations."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ReleaseStatus:
    """Current local release metadata for operator-facing status panels."""

    version: str
    milestone: str
    status: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "milestone": self.milestone,
            "status": self.status,
        }


def build_release_status(root_path: str | Path = ".") -> ReleaseStatus:
    """Build release metadata without changing the frozen public API status contract."""

    root = Path(root_path)
    version = _read_version(root)
    return ReleaseStatus(
        version=version,
        milestone=_derive_milestone(version),
        status="operational",
    )


def _read_version(root: Path) -> str:
    version_path = root / "VERSION"
    if not version_path.exists():
        return "unknown"
    return version_path.read_text(encoding="utf-8").strip() or "unknown"


def _derive_milestone(version: str) -> str:
    if version.startswith("0.6.0-alpha"):
        suffix = version.removeprefix("0.6.0-alpha")
        if suffix.isdigit():
            return f"M6.{suffix}"
    if version.startswith("0.5.0-alpha"):
        suffix = version.removeprefix("0.5.0-alpha")
        if suffix.isdigit():
            return f"M5.{suffix}"
    if version == "0.4.0":
        return "M4.12"
    return "unknown"
