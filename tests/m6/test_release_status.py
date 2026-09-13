"""Tests for M6 release status metadata."""
from __future__ import annotations

from pathlib import Path

from skos.m6.production import build_release_status


def current_version() -> str:
    return Path("VERSION").read_text(encoding="utf-8").strip()


def test_release_status_reads_current_version() -> None:
    status = build_release_status()

    assert status.version == current_version()
    assert status.milestone.startswith("M6.")
    assert status.status == "operational"


def test_release_status_serializes_to_dict() -> None:
    data = build_release_status().as_dict()

    assert data["version"] == current_version()
    assert data["milestone"].startswith("M6.")
    assert data["status"] == "operational"
