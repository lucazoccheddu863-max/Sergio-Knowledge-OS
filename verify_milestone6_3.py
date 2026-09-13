#!/usr/bin/env python3
"""Verify script for M6.3 — Backup Manifest."""
from __future__ import annotations

import pathlib
import subprocess
import sys


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, capture_output=True, text=True)


def main() -> int:
    print("=" * 60)
    print("M6.3 Verify — Backup Manifest")
    print("=" * 60)

    print("\n[1/5] Running M6 tests...")
    result = run([sys.executable, "-m", "pytest", "tests/m6/", "-q"])
    if result.returncode == 0 and "10 passed" in result.stdout:
        print("  OK M6 tests PASS (10/10)")
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
    if version == "0.6.0-alpha3" and "M6.3" in changelog:
        print(f"  OK VERSION = {version}; CHANGELOG includes M6.3")
    else:
        print("  FAILED version or changelog")
        return 1

    print("\n[5/5] Checking backup manifest import...")
    from skos.m4.infrastructure.adapters.config.hierarchical_config_adapter import (
        HierarchicalConfigAdapter,
    )
    from skos.m6.production import build_backup_manifest

    manifest = build_backup_manifest(HierarchicalConfigAdapter(defaults={}))
    if "items" in manifest.as_dict():
        print("  OK backup manifest import PASS")
    else:
        print("  FAILED backup manifest import")
        return 1

    print("\n" + "=" * 60)
    print("M6.3 verification complete. All checks PASS.")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
