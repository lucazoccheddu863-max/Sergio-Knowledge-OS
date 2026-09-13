#!/usr/bin/env python3
"""Setup script for M6.3 — Backup Manifest."""
from __future__ import annotations

import pathlib
import sys


def main() -> int:
    print("=" * 60)
    print("M6.3 Setup — Backup Manifest")
    print("=" * 60)

    print("\n[1/4] Checking M6.3 files...")
    files = [
        "skos/m6/production/backup.py",
        "tests/m6/test_backup_manifest.py",
    ]
    for file_path in files:
        if pathlib.Path(file_path).exists():
            print(f"  OK {file_path}")
        else:
            print(f"  MISSING {file_path}")
            return 1

    print("\n[2/4] Checking backup manifest import...")
    from skos.m4.infrastructure.adapters.config.hierarchical_config_adapter import (
        HierarchicalConfigAdapter,
    )
    from skos.m6.production import build_backup_manifest

    manifest = build_backup_manifest(HierarchicalConfigAdapter(defaults={}))
    if isinstance(manifest.as_dict(), dict):
        print("  OK backup manifest import and serialization")
    else:
        print("  FAILED backup manifest serialization")
        return 1

    print("\n[3/4] Checking version consistency...")
    version = pathlib.Path("VERSION").read_text(encoding="utf-8").strip()
    if version == "0.6.0-alpha3":
        print(f"  OK VERSION = {version}")
    else:
        print(f"  FAILED VERSION = {version} (expected 0.6.0-alpha3)")
        return 1

    print("\n[4/4] Checking changelog...")
    changelog = pathlib.Path("CHANGELOG.md").read_text(encoding="utf-8")
    if "M6.3" in changelog and "0.6.0-alpha3" in changelog:
        print("  OK CHANGELOG includes M6.3")
    else:
        print("  FAILED CHANGELOG missing M6.3")
        return 1

    print("\n" + "=" * 60)
    print("M6.3 setup complete. Run: python verify_milestone6_3.py")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
