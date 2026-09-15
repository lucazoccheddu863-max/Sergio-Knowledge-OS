#!/usr/bin/env python3
"""Setup script for M6.11 — Admin Smoke Check."""
from __future__ import annotations

import pathlib
import sys


def main() -> int:
    print("=" * 60)
    print("M6.11 Setup — Admin Smoke Check")
    print("=" * 60)

    print("\n[1/4] Checking smoke check files...")
    files = [
        "skos/m6/production/overview.py",
        "tests/m6/test_admin_overview.py",
        "skos/m5/admin_console/assets/index.html",
        "skos/m5/admin_console/assets/app.js",
    ]
    for file_path in files:
        if pathlib.Path(file_path).exists():
            print(f"  OK {file_path}")
        else:
            print(f"  MISSING {file_path}")
            return 1

    print("\n[2/4] Checking smoke endpoint wiring...")
    api_text = pathlib.Path("skos/m4/infrastructure/adapters/api/fastapi_adapter.py").read_text(
        encoding="utf-8"
    )
    js_text = pathlib.Path("skos/m5/admin_console/assets/app.js").read_text(encoding="utf-8")
    if "/api/v1/admin/smoke" in api_text and "/api/v1/admin/smoke" in js_text:
        print("  OK admin smoke wiring available")
    else:
        print("  FAILED admin smoke wiring missing")
        return 1

    print("\n[3/4] Checking version consistency...")
    version = pathlib.Path("VERSION").read_text(encoding="utf-8").strip()
    if version == "0.6.0-alpha11":
        print(f"  OK VERSION = {version}")
    else:
        print(f"  FAILED VERSION = {version} (expected 0.6.0-alpha11)")
        return 1

    print("\n[4/4] Checking changelog...")
    changelog = pathlib.Path("CHANGELOG.md").read_text(encoding="utf-8")
    if "M6.11" in changelog and "0.6.0-alpha11" in changelog:
        print("  OK CHANGELOG includes M6.11")
    else:
        print("  FAILED CHANGELOG missing M6.11")
        return 1

    print("\n" + "=" * 60)
    print("M6.11 setup complete. Run: python verify_milestone6_11.py")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
