#!/usr/bin/env python3
"""Verify script for M4.11 — Security & Auth."""
from __future__ import annotations
import subprocess
import sys

def main() -> int:
    print("=" * 60)
    print("M4.11 Verify — Security & Auth")
    print("=" * 60)

    print("\n[1/3] Running M4.11 tests...")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/m4/test_security.py", "-v"],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        print("  ✅ M4.11 tests PASS")
    else:
        print("  ❌ M4.11 tests FAILED")
        print(result.stdout)
        return 1

    print("\n[2/3] Running regression tests...")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/m4/", "-v", "--tb=short"],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        print("  ✅ Regression tests PASS")
    else:
        print("  ❌ Regression tests FAILED")
        print(result.stdout[-2000:])
        return 1

    print("\n[3/3] Checking version consistency...")
    with open("skos/m4/infrastructure/adapters/api/fastapi_adapter.py") as f:
        content = f.read()
    if "0.4.0-alpha13" in content and "M4.11" in content:
        print("  ✅ Version consistent")
    else:
        print("  ❌ Version inconsistent")
        return 1

    print("\n" + "=" * 60)
    print("M4.11 verification complete. All checks PASS.")
    print("=" * 60)
    return 0

if __name__ == "__main__":
    sys.exit(main())
