"""Tests for the M6 operator manual."""
from __future__ import annotations

from skos.m6.production import build_operator_manual


def test_operator_manual_has_core_sections() -> None:
    manual = build_operator_manual()

    assert manual.title == "Sergio Knowledge OS Operator Manual"
    assert {section.title for section in manual.sections} >= {
        "Start",
        "Daily Check",
        "Backup",
        "Release",
    }


def test_operator_manual_serializes_to_dict() -> None:
    data = build_operator_manual().as_dict()

    assert data["audience"] == "Local operator"
    assert data["sections"]
    assert data["sections"][0]["steps"]


def test_operator_manual_mentions_safe_restore_and_release_gate() -> None:
    text = str(build_operator_manual().as_dict())

    assert "empty staging directory" in text
    assert "readiness gate" in text
