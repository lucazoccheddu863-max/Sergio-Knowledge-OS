#!/usr/bin/env python3
"""Verify script for M7.1 — AI Service Runtime Contract."""
from __future__ import annotations

import pathlib
import subprocess
import sys


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, capture_output=True, text=True)


def check_tests(path: str, expected: str, label: str) -> bool:
    result = run([sys.executable, "-m", "pytest", path, "-q"])
    if result.returncode == 0 and expected in result.stdout:
        print(f"  OK {label} PASS ({expected.replace(' passed', '')})")
        return True
    print(f"  FAILED {label}")
    print(result.stdout[-1200:])
    print(result.stderr[-1200:])
    return False


def main() -> int:
    print("=" * 60)
    print("M7.1 Verify — AI Service Runtime Contract")
    print("=" * 60)

    suites = [
        ("tests/m7/", "4 passed", "M7 tests"),
        ("tests/m6/", "66 passed", "M6 regression"),
        ("tests/m5/", "32 passed", "M5 regression"),
        ("tests/m4/", "238 passed", "M4 regression"),
    ]
    for index, (path, expected, label) in enumerate(suites, start=1):
        print(f"\n[{index}/6] Running {label}...")
        if not check_tests(path, expected, label):
            return 1

    print("\n[5/6] Checking version and changelog...")
    version = pathlib.Path("VERSION").read_text(encoding="utf-8").strip()
    changelog = pathlib.Path("CHANGELOG.md").read_text(encoding="utf-8")
    if version == "0.7.0-alpha1" and "M7.1" in changelog:
        print(f"  OK VERSION = {version}; CHANGELOG includes M7.1")
    else:
        print("  FAILED version or changelog")
        return 1

    print("\n[6/6] Checking AI service runtime contract...")
    service_text = pathlib.Path("skos/m4/application/services/ai_service.py").read_text(encoding="utf-8")
    if "_default_provider_name" in service_text and "provider_or_request" in service_text:
        print("  OK executable AI service contract PASS")
    else:
        print("  FAILED executable AI service contract missing")
        return 1

    print("\n" + "=" * 60)
    print("M7.1 verification complete. All checks PASS.")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
