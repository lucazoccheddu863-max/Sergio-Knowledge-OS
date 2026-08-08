#!/usr/bin/env python3
"""Verification script for M4.9 — REST API Adapter."""
from __future__ import annotations

import subprocess
import sys


def main() -> int:
    print("=" * 60)
    print("M4.9 Verification — REST API Adapter")
    print("=" * 60)

    print("\n[1/2] Running M4.9 tests...")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/m4/test_api_adapter.py", "-v"],
        capture_output=False,
    )
    if result.returncode != 0:
        print("    ❌ M4.9 tests FAILED")
        return 1
    print("    ✅ M4.9 tests PASSED")

    print("\n[2/2] Running regression tests (M4.1–M4.8)...")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/m4/", "-v", "--ignore=tests/m4/test_api_adapter.py"],
        capture_output=False,
    )
    if result.returncode != 0:
        print("    ❌ Regression tests FAILED")
        return 1
    print("    ✅ Regression tests PASSED")

    print("\n" + "=" * 60)
    print("M4.9 VERIFICATION COMPLETE")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
