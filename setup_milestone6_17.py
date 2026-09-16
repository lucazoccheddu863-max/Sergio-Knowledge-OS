#!/usr/bin/env python3
"""Setup script for M6.17 — Local Workspace Bootstrap."""
from __future__ import annotations

import pathlib
import sys


def main() -> int:
    print("=" * 60)
    print("M6.17 Setup — Local Workspace Bootstrap")
    print("=" * 60)

    print("\n[1/4] Checking local bootstrap files...")
    files = [
        "skos/m6/production/launch.py",
        "tests/m6/test_local_launch.py",
        "skos/m5/admin_console/assets/index.html",
        "skos/m5/admin_console/assets/app.js",
    ]
    for file_path in files:
        if pathlib.Path(file_path).exists():
            print(f"  OK {file_path}")
        else:
            print(f"  MISSING {file_path}")
            return 1

    print("\n[2/4] Checking local bootstrap wiring...")
    api_text = pathlib.Path("skos/m4/infrastructure/adapters/api/fastapi_adapter.py").read_text(
        encoding="utf-8"
    )
    js_text = pathlib.Path("skos/m5/admin_console/assets/app.js").read_text(encoding="utf-8")
    route = "/api/v1/admin/local/bootstrap"
    if route in api_text and route in js_text:
        print("  OK local bootstrap endpoint available")
    else:
        print("  FAILED local bootstrap endpoint missing")
        return 1

    print("\n[3/4] Checking version consistency...")
    version = pathlib.Path("VERSION").read_text(encoding="utf-8").strip()
    if version == "0.6.0-alpha17":
        print(f"  OK VERSION = {version}")
    else:
        print(f"  FAILED VERSION = {version} (expected 0.6.0-alpha17)")
        return 1

    print("\n[4/4] Checking changelog...")
    changelog = pathlib.Path("CHANGELOG.md").read_text(encoding="utf-8")
    if "M6.17" in changelog and "0.6.0-alpha17" in changelog:
        print("  OK CHANGELOG includes M6.17")
    else:
        print("  FAILED CHANGELOG missing M6.17")
        return 1

    print("\n" + "=" * 60)
    print("M6.17 setup complete. Run: python verify_milestone6_17.py")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
