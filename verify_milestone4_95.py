#!/usr/bin/env python3
"""Verification script for M4.9.5 — API Contract Freeze."""
from __future__ import annotations

import subprocess
import sys


def main() -> int:
    print("=" * 60)
    print("M4.9.5 Verification — API Contract Freeze")
    print("=" * 60)

    print("\n[1/3] Running M4.9.5 tests...")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/m4/test_api_adapter.py", "-v"],
        capture_output=False,
    )
    if result.returncode != 0:
        print("    ❌ M4.9.5 tests FAILED")
        return 1
    print("    ✅ M4.9.5 tests PASSED")

    print("\n[2/3] Running regression tests (M4.1–M4.9)...")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/m4/", "-v", "--ignore=tests/m4/test_api_adapter.py"],
        capture_output=False,
    )
    if result.returncode != 0:
        print("    ❌ Regression tests FAILED")
        return 1
    print("    ✅ Regression tests PASSED")

    print("\n[3/3] Verifying OpenAPI schema generation...")
    result = subprocess.run(
        [sys.executable, "-c",
         "from skos.m4.infrastructure.adapters.api import FastAPIAdapter; "
         "from unittest.mock import Mock; "
         "app = FastAPIAdapter(orchestrator=Mock(), config=Mock()).app; "
         "assert app.openapi() is not None; "
         "print('OpenAPI schema generated successfully')"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print("    ❌ OpenAPI schema generation FAILED")
        print(result.stderr)
        return 1
    print("    ✅ OpenAPI schema generation PASSED")

    print("\n" + "=" * 60)
    print("M4.9.5 VERIFICATION COMPLETE")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
