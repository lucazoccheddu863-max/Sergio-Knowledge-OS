#!/usr/bin/env python3
"""Verify script for M5.1 — Persistence Layer."""
from __future__ import annotations
import subprocess
import sys

def main() -> int:
    print("=" * 60)
    print("M5.1 Verify — Persistence Layer")
    print("=" * 60)

    print("\n[1/4] Running M5.1 tests...")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/m5/test_persistence.py", "-v"],
        capture_output=True, text=True,
    )
    if result.returncode == 0 and "passed" in result.stdout:
        passed = result.stdout.count(" PASSED ")
        print(f"  ✅ M5.1 tests PASS ({passed} tests)")
    else:
        print("  ❌ M5.1 tests FAILED")
        print(result.stdout[-1000:])
        return 1

    print("\n[2/4] Running M4 regression tests...")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/m4/", "-q", "--tb=short"],
        capture_output=True, text=True,
    )
    if result.returncode == 0 and "238 passed" in result.stdout:
        print("  ✅ M4 regression PASS (238/238)")
    else:
        print("  ❌ M4 regression FAILED")
        print(result.stdout[-1000:])
        return 1

    print("\n[3/4] Checking version...")
    with open("VERSION") as f:
        v = f.read().strip()
    if v == "0.5.0-alpha1":
        print(f"  ✅ VERSION = {v}")
    else:
        print(f"  ❌ VERSION = {v} (expected 0.5.0-alpha1)")
        return 1

    print("\n[4/4] Checking CHANGELOG...")
    with open("CHANGELOG.md") as f:
        content = f.read()
    if "M5.1" in content and "0.5.0-alpha1" in content:
        print("  ✅ CHANGELOG includes M5.1")
    else:
        print("  ❌ CHANGELOG missing M5.1")
        return 1

    print("\n" + "=" * 60)
    print("M5.1 verification complete. All checks PASS.")
    print("=" * 60)
    return 0

if __name__ == "__main__":
    sys.exit(main())
