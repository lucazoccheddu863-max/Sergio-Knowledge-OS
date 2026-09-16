#!/usr/bin/env python3
"""Verify script for M6.18 — Admin Console UX Polish."""
from __future__ import annotations

import pathlib
import subprocess
import sys


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, capture_output=True, text=True)


def main() -> int:
    print("=" * 60)
    print("M6.18 Verify — Admin Console UX Polish")
    print("=" * 60)

    print("\n[1/5] Running M6 tests...")
    result = run([sys.executable, "-m", "pytest", "tests/m6/", "-q"])
    if result.returncode == 0 and "57 passed" in result.stdout:
        print("  OK M6 tests PASS (57/57)")
    else:
        print("  FAILED M6 tests")
        print(result.stdout[-1200:])
        print(result.stderr[-1200:])
        return 1

    print("\n[2/5] Running M5 regression tests...")
    result = run([sys.executable, "-m", "pytest", "tests/m5/", "-q"])
    if result.returncode == 0 and "32 passed" in result.stdout:
        print("  OK M5 regression PASS (32/32)")
    else:
        print("  FAILED M5 regression")
        print(result.stdout[-1200:])
        print(result.stderr[-1200:])
        return 1

    print("\n[3/5] Running M4 regression tests...")
    result = run([sys.executable, "-m", "pytest", "tests/m4/", "-q", "--tb=short"])
    if result.returncode == 0 and "238 passed" in result.stdout:
        print("  OK M4 regression PASS (238/238)")
    else:
        print("  FAILED M4 regression")
        print(result.stdout[-1200:])
        print(result.stderr[-1200:])
        return 1

    print("\n[4/5] Checking version and changelog...")
    version = pathlib.Path("VERSION").read_text(encoding="utf-8").strip()
    changelog = pathlib.Path("CHANGELOG.md").read_text(encoding="utf-8")
    if version == "0.6.0-alpha18" and "M6.18" in changelog:
        print(f"  OK VERSION = {version}; CHANGELOG includes M6.18")
    else:
        print("  FAILED version or changelog")
        return 1

    print("\n[5/5] Checking admin console UX helpers...")
    js_text = pathlib.Path("skos/m5/admin_console/assets/app.js").read_text(encoding="utf-8")
    css_text = pathlib.Path("skos/m5/admin_console/assets/styles.css").read_text(encoding="utf-8")
    if "setManualRows" in js_text and "manual-step" in css_text and "overflow-wrap: anywhere" in css_text:
        print("  OK admin console UX helpers PASS")
    else:
        print("  FAILED admin console UX helpers missing")
        return 1

    print("\n" + "=" * 60)
    print("M6.18 verification complete. All checks PASS.")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
