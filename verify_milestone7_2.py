#!/usr/bin/env python3
"""Verify script for M7.2 — Complete Application Runtime Assembly."""
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
    print("M7.2 Verify — Complete Application Runtime Assembly")
    print("=" * 60)

    suites = [
        ("tests/m7/", "8 passed", "M7 tests"),
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
    if version == "0.7.0-alpha2" and "M7.2" in changelog:
        print(f"  OK VERSION = {version}; CHANGELOG includes M7.2")
    else:
        print("  FAILED version or changelog")
        return 1

    print("\n[6/6] Checking complete runtime assembly...")
    factory = pathlib.Path("skos/m7/runtime/application_factory.py").read_text(encoding="utf-8")
    if "ApplicationRuntime" in factory and "ApplicationEventBus" in factory:
        print("  OK complete runtime assembly PASS")
    else:
        print("  FAILED complete runtime assembly missing")
        return 1

    print("\n" + "=" * 60)
    print("M7.2 verification complete. All checks PASS.")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
