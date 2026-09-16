#!/usr/bin/env python3
"""Setup script for M7.1 — AI Service Runtime Contract."""
from __future__ import annotations

import pathlib
import sys


def main() -> int:
    print("=" * 60)
    print("M7.1 Setup — AI Service Runtime Contract")
    print("=" * 60)

    print("\n[1/4] Checking runtime contract files...")
    files = [
        "skos/m4/application/services/ai_service.py",
        "tests/m7/test_ai_service_contract.py",
        "pyproject.toml",
    ]
    for file_path in files:
        if pathlib.Path(file_path).exists():
            print(f"  OK {file_path}")
        else:
            print(f"  MISSING {file_path}")
            return 1

    print("\n[2/4] Checking structured request support...")
    service_text = pathlib.Path("skos/m4/application/services/ai_service.py").read_text(encoding="utf-8")
    if "str | ChatRequest" in service_text and "str | EmbeddingRequest" in service_text:
        print("  OK structured AI request contract available")
    else:
        print("  FAILED structured AI request contract missing")
        return 1

    print("\n[3/4] Checking version consistency...")
    version = pathlib.Path("VERSION").read_text(encoding="utf-8").strip()
    if version == "0.7.0-alpha1":
        print(f"  OK VERSION = {version}")
    else:
        print(f"  FAILED VERSION = {version} (expected 0.7.0-alpha1)")
        return 1

    print("\n[4/4] Checking changelog...")
    changelog = pathlib.Path("CHANGELOG.md").read_text(encoding="utf-8")
    if "M7.1" in changelog and "0.7.0-alpha1" in changelog:
        print("  OK CHANGELOG includes M7.1")
    else:
        print("  FAILED CHANGELOG missing M7.1")
        return 1

    print("\n" + "=" * 60)
    print("M7.1 setup complete. Run: python verify_milestone7_1.py")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
