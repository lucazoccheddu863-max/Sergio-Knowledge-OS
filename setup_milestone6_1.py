#!/usr/bin/env python3
"""Setup script for M6.1 — Production Readiness."""
from __future__ import annotations

import pathlib
import sys


def main() -> int:
    print("=" * 60)
    print("M6.1 Setup — Production Readiness")
    print("=" * 60)

    print("\n[1/4] Checking M6 files...")
    files = [
        "skos/m6/__init__.py",
        "skos/m6/production/__init__.py",
        "skos/m6/production/readiness.py",
        "tests/m6/test_readiness.py",
    ]
    for file_path in files:
        if pathlib.Path(file_path).exists():
            print(f"  OK {file_path}")
        else:
            print(f"  MISSING {file_path}")
            return 1

    print("\n[2/4] Checking readiness import...")
    from skos.m4.infrastructure.adapters.config.hierarchical_config_adapter import (
        HierarchicalConfigAdapter,
    )
    from skos.m6.production import run_production_readiness

    config = HierarchicalConfigAdapter(defaults={"m6": {"environment": "development"}})
    report = run_production_readiness(config)
    if report.as_dict()["environment"] == "development":
        print("  OK readiness checker import and report")
    else:
        print("  FAILED readiness checker report")
        return 1

    print("\n[3/4] Checking version consistency...")
    version = pathlib.Path("VERSION").read_text(encoding="utf-8").strip()
    if version == "0.6.0-alpha1":
        print(f"  OK VERSION = {version}")
    else:
        print(f"  FAILED VERSION = {version} (expected 0.6.0-alpha1)")
        return 1

    print("\n[4/4] Checking config and changelog...")
    config_text = pathlib.Path("config.yaml").read_text(encoding="utf-8")
    changelog = pathlib.Path("CHANGELOG.md").read_text(encoding="utf-8")
    if "m6:" in config_text and "M6.1" in changelog and "0.6.0-alpha1" in changelog:
        print("  OK M6 config and changelog")
    else:
        print("  FAILED M6 config or changelog missing")
        return 1

    print("\n" + "=" * 60)
    print("M6.1 setup complete. Run: python verify_milestone6_1.py")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
