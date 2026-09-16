#!/usr/bin/env python3
"""Verify M7.3 — Safe Document Import and all frozen regressions."""
from __future__ import annotations

import pathlib
import subprocess
import sys


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, capture_output=True, text=True)


def check_tests(path: str, expected: str, label: str) -> bool:
    result = run([sys.executable, "-m", "pytest", path, "-q"])
    if result.returncode == 0 and expected in result.stdout:
        print(f"OK {label} ({expected})")
        return True
    print(f"FAILED {label}")
    print(result.stdout[-1200:])
    print(result.stderr[-1200:])
    return False


def main() -> int:
    print("=" * 60)
    print("M7.3 Verify — Safe Document Import")
    print("=" * 60)
    suites = [
        ("tests/m7/", "12 passed", "M7 tests"),
        ("tests/m6/", "67 passed", "M6 regression"),
        ("tests/m5/", "32 passed", "M5 regression"),
        ("tests/m4/", "238 passed", "M4 regression"),
    ]
    for path, expected, label in suites:
        if not check_tests(path, expected, label):
            return 1

    version = pathlib.Path("VERSION").read_text(encoding="utf-8").strip()
    changelog = pathlib.Path("CHANGELOG.md").read_text(encoding="utf-8")
    if version != "0.7.0-alpha3" or "M7.3" not in changelog:
        print("FAILED version or changelog")
        return 1
    source = pathlib.Path("skos/m7/runtime/document_import.py").read_text(encoding="utf-8")
    if "sha256" not in source or "DocumentImportService" not in source:
        print("FAILED document import implementation")
        return 1
    print("OK release metadata and document import implementation")
    print("M7.3 verification complete. All checks PASS.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
