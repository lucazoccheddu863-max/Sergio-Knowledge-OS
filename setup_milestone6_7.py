#!/usr/bin/env python3
"""Setup script for M6.7 — Admin Backup API."""
from __future__ import annotations

import pathlib
import sys


def main() -> int:
    print("=" * 60)
    print("M6.7 Setup — Admin Backup API")
    print("=" * 60)

    print("\n[1/4] Checking admin backup API files...")
    files = [
        "skos/m4/infrastructure/adapters/api/fastapi_adapter.py",
        "tests/m6/test_admin_readiness_api.py",
    ]
    for file_path in files:
        if pathlib.Path(file_path).exists():
            print(f"  OK {file_path}")
        else:
            print(f"  MISSING {file_path}")
            return 1

    print("\n[2/4] Checking admin backup route wiring...")
    api_text = pathlib.Path("skos/m4/infrastructure/adapters/api/fastapi_adapter.py").read_text(
        encoding="utf-8"
    )
    required_routes = (
        "/api/v1/admin/backup/manifest",
        "/api/v1/admin/backup/create",
        "/api/v1/admin/backup/inspect",
        "/api/v1/admin/backup/restore/stage",
    )
    missing = [route for route in required_routes if route not in api_text]
    if missing:
        print(f"  FAILED missing routes: {', '.join(missing)}")
        return 1
    print("  OK admin backup routes available")

    print("\n[3/4] Checking version consistency...")
    version = pathlib.Path("VERSION").read_text(encoding="utf-8").strip()
    if version == "0.6.0-alpha7":
        print(f"  OK VERSION = {version}")
    else:
        print(f"  FAILED VERSION = {version} (expected 0.6.0-alpha7)")
        return 1

    print("\n[4/4] Checking changelog...")
    changelog = pathlib.Path("CHANGELOG.md").read_text(encoding="utf-8")
    if "M6.7" in changelog and "0.6.0-alpha7" in changelog:
        print("  OK CHANGELOG includes M6.7")
    else:
        print("  FAILED CHANGELOG missing M6.7")
        return 1

    print("\n" + "=" * 60)
    print("M6.7 setup complete. Run: python verify_milestone6_7.py")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
