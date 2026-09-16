"""Operator manual content for SKOS local use."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class OperatorManualStep:
    """Single operator action in the local manual."""

    title: str
    detail: str

    def as_dict(self) -> dict[str, str]:
        return {"title": self.title, "detail": self.detail}


@dataclass(frozen=True)
class OperatorManualSection:
    """A section of the operator manual."""

    title: str
    steps: tuple[OperatorManualStep, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "steps": [step.as_dict() for step in self.steps],
        }


@dataclass(frozen=True)
class OperatorManual:
    """Structured manual for running and checking SKOS locally."""

    title: str
    audience: str
    sections: tuple[OperatorManualSection, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "audience": self.audience,
            "sections": [section.as_dict() for section in self.sections],
        }


def build_operator_manual() -> OperatorManual:
    """Build the operator-facing local manual."""

    return OperatorManual(
        title="Sergio Knowledge OS Operator Manual",
        audience="Local operator",
        sections=(
            OperatorManualSection(
                title="Start",
                steps=(
                    OperatorManualStep(
                        "Run local server",
                        "Use the Local Launch command and keep that terminal window open.",
                    ),
                    OperatorManualStep(
                        "Open admin console",
                        "Open the Admin URL shown by Local Launch.",
                    ),
                ),
            ),
            OperatorManualSection(
                title="Daily Check",
                steps=(
                    OperatorManualStep(
                        "Refresh dashboard",
                        "Confirm status, readiness, smoke check and local launch are ready.",
                    ),
                    OperatorManualStep(
                        "Inspect warnings",
                        "If a panel says Needs attention, read its warnings before continuing.",
                    ),
                ),
            ),
            OperatorManualSection(
                title="Backup",
                steps=(
                    OperatorManualStep(
                        "Create backup",
                        "Use Backup Operations to create a ZIP before important changes.",
                    ),
                    OperatorManualStep(
                        "Stage restore",
                        "Restore only into an empty staging directory, never over live data.",
                    ),
                ),
            ),
            OperatorManualSection(
                title="Release",
                steps=(
                    OperatorManualStep(
                        "Run readiness gate",
                        "Use Release Package to create and inspect a fresh release ZIP.",
                    ),
                    OperatorManualStep(
                        "Distribute only ready packages",
                        "A package is distributable only when the gate reports ready with no warnings.",
                    ),
                ),
            ),
        ),
    )
