#!/usr/bin/env python3
"""Setup script for M6.8 — Admin Backup Console."""
from __future__ import annotations

import pathlib
import sys


def main() -> int:
    print("=" * 60)
    print("M6.8 Setup — Admin Backup Console")
    print("=" * 60)

    print("\n[1/4] Checking admin console assets...")
    files = [
        "skos/m5/admin_console/assets/index.html",
        "skos/m5/admin_console/assets/app.js",
        "skos/m5/admin_console/assets/styles.css",
        "tests/m6/test_admin_readiness_api.py",
    ]
    for file_path in files:
        if pathlib.Path(file_path).exists():
            print(f"  OK {file_path}")
        else:
            print(f"  MISSING {file_path}")
            return 1

    print("\n[2/4] Checking backup console wiring...")
    html = pathlib.Path("skos/m5/admin_console/assets/index.html").read_text(encoding="utf-8")
    js = pathlib.Path("skos/m5/admin_console/assets/app.js").read_text(encoding="utf-8")
    if "Backup Operations" in html and "/api/v1/admin/backup/restore/stage" in js:
        print("  OK backup console wiring available")
    else:
        print("  FAILED backup console wiring missing")
        return 1

    print("\n[3/4] Checking version consistency...")
    version = pathlib.Path("VERSION").read_text(encoding="utf-8").strip()
    if version == "0.6.0-alpha8":
        print(f"  OK VERSION = {version}")
    else:
        print(f"  FAILED VERSION = {version} (expected 0.6.0-alpha8)")
        return 1

    print("\n[4/4] Checking changelog...")
    changelog = pathlib.Path("CHANGELOG.md").read_text(encoding="utf-8")
    if "M6.8" in changelog and "0.6.0-alpha8" in changelog:
        print("  OK CHANGELOG includes M6.8")
    else:
        print("  FAILED CHANGELOG missing M6.8")
        return 1

    print("\n" + "=" * 60)
    print("M6.8 setup complete. Run: python verify_milestone6_8.py")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
