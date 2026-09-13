#!/usr/bin/env python3
"""Setup script for M6.5 — Backup Restore Inspection."""
from __future__ import annotations

import pathlib
import sys


def main() -> int:
    print("=" * 60)
    print("M6.5 Setup — Backup Restore Inspection")
    print("=" * 60)

    print("\n[1/4] Checking restore inspection files...")
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

    print("\n[2/4] Checking restore inspection import...")
    from skos.m6.production import BackupArchiveInspection, inspect_backup_archive

    if BackupArchiveInspection and inspect_backup_archive:
        print("  OK restore inspection API available")
    else:
        print("  FAILED restore inspection API missing")
        return 1

    print("\n[3/4] Checking version consistency...")
    version = pathlib.Path("VERSION").read_text(encoding="utf-8").strip()
    if version == "0.6.0-alpha5":
        print(f"  OK VERSION = {version}")
    else:
        print(f"  FAILED VERSION = {version} (expected 0.6.0-alpha5)")
        return 1

    print("\n[4/4] Checking changelog...")
    changelog = pathlib.Path("CHANGELOG.md").read_text(encoding="utf-8")
    if "M6.5" in changelog and "0.6.0-alpha5" in changelog:
        print("  OK CHANGELOG includes M6.5")
    else:
        print("  FAILED CHANGELOG missing M6.5")
        return 1

    print("\n" + "=" * 60)
    print("M6.5 setup complete. Run: python verify_milestone6_5.py")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
