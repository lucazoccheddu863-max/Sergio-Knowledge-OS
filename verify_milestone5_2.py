#!/usr/bin/env python3
"""Verify script for M5.2 — Runtime Wiring."""
from __future__ import annotations

import pathlib
import subprocess
import sys


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, capture_output=True, text=True)


def main() -> int:
    print("=" * 60)
    print("M5.2 Verify — Runtime Wiring")
    print("=" * 60)

    print("\n[1/5] Running M5 tests...")
    result = run([sys.executable, "-m", "pytest", "tests/m5/", "-q"])
    if result.returncode == 0 and "29 passed" in result.stdout:
        print("  OK M5 tests PASS (29/29)")
    else:
        print("  FAILED M5 tests")
        print(result.stdout[-1200:])
        print(result.stderr[-1200:])
        return 1

    print("\n[2/5] Running M4 regression tests...")
    result = run([sys.executable, "-m", "pytest", "tests/m4/", "-q", "--tb=short"])
    if result.returncode == 0 and "238 passed" in result.stdout:
        print("  OK M4 regression PASS (238/238)")
    else:
        print("  FAILED M4 regression")
        print(result.stdout[-1200:])
        print(result.stderr[-1200:])
        return 1

    print("\n[3/5] Checking version...")
    version = pathlib.Path("VERSION").read_text(encoding="utf-8").strip()
    if version == "0.5.0-alpha2":
        print(f"  OK VERSION = {version}")
    else:
        print(f"  FAILED VERSION = {version} (expected 0.5.0-alpha2)")
        return 1

    print("\n[4/5] Checking changelog...")
    changelog = pathlib.Path("CHANGELOG.md").read_text(encoding="utf-8")
    if "M5.2" in changelog and "0.5.0-alpha2" in changelog:
        print("  OK CHANGELOG includes M5.2")
    else:
        print("  FAILED CHANGELOG missing M5.2")
        return 1

    print("\n[5/5] Checking runtime import...")
    from skos.m4.infrastructure.adapters.config.hierarchical_config_adapter import (
        HierarchicalConfigAdapter,
    )
    from skos.m5.runtime import build_persistence_runtime

    runtime = build_persistence_runtime(
        HierarchicalConfigAdapter(defaults={"m5": {"persistence": {"mode": "memory"}}})
    )
    if runtime.health().healthy:
        print("  OK runtime health PASS")
    else:
        print("  FAILED runtime health")
        return 1

    print("\n" + "=" * 60)
    print("M5.2 verification complete. All checks PASS.")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
