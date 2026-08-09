#!/usr/bin/env python3
"""Verification script for M4.10 — Observability & Operations Adapter."""
from __future__ import annotations
import subprocess
import sys

def main() -> int:
    print("=" * 60)
    print("M4.10 Verification — Observability & Operations Adapter")
    print("=" * 60)

    print("\n[1/3] Running M4.10 tests...")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/m4/test_observability.py", "-v"],
        capture_output=False,
    )
    if result.returncode != 0:
        print("    ❌ M4.10 tests FAILED")
        return 1
    print("    ✅ M4.10 tests PASSED")

    print("\n[2/3] Running regression tests (M4.1–M4.9.5)...")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/m4/", "-v", "--ignore=tests/m4/test_observability.py"],
        capture_output=False,
    )
    if result.returncode != 0:
        print("    ❌ Regression tests FAILED")
        return 1
    print("    ✅ Regression tests PASSED")

    print("\n[3/3] Verifying /metrics endpoint...")
    result = subprocess.run(
        [sys.executable, "-c",
         "from unittest.mock import Mock; "
         "from skos.m4.infrastructure.adapters.api import FastAPIAdapter; "
         "from skos.m4.infrastructure.adapters.observability import PrometheusMetricsAdapter; "
         "m = PrometheusMetricsAdapter(); "
         "app = FastAPIAdapter(orchestrator=Mock(), config=Mock(), metrics=m).app; "
         "from fastapi.testclient import TestClient; "
         "c = TestClient(app); "
         "r = c.get('/metrics'); "
         "assert r.status_code == 200; "
         "print('/metrics OK')"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print("    ❌ /metrics endpoint FAILED")
        print(result.stderr)
        return 1
    print("    ✅ /metrics endpoint PASSED")

    print("\n" + "=" * 60)
    print("M4.10 VERIFICATION COMPLETE")
    print("=" * 60)
    return 0

if __name__ == "__main__":
    sys.exit(main())
