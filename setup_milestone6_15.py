#!/usr/bin/env python3
"""Setup script for M6.15 — Local Launch Preflight."""
from __future__ import annotations

import pathlib
import sys


def main() -> int:
    print("=" * 60)
    print("M6.15 Setup — Local Launch Preflight")
    print("=" * 60)

    print("\n[1/4] Checking local launch files...")
    files = [
        "skos/m6/production/launch.py",
        "skos/m6/production/local_server.py",
        "tests/m6/test_local_launch.py",
        "skos/m5/admin_console/assets/app.js",
    ]
    for file_path in files:
        if pathlib.Path(file_path).exists():
            print(f"  OK {file_path}")
        else:
            print(f"  MISSING {file_path}")
            return 1

    print("\n[2/4] Checking local launch wiring...")
    api_text = pathlib.Path("skos/m4/infrastructure/adapters/api/fastapi_adapter.py").read_text(
        encoding="utf-8"
    )
    js_text = pathlib.Path("skos/m5/admin_console/assets/app.js").read_text(encoding="utf-8")
    route = "/api/v1/admin/local/launch"
    if route in api_text and route in js_text:
        print("  OK local launch endpoint available")
    else:
        print("  FAILED local launch endpoint missing")
        return 1

    print("\n[3/4] Checking version consistency...")
    version = pathlib.Path("VERSION").read_text(encoding="utf-8").strip()
    if version == "0.6.0-alpha15":
        print(f"  OK VERSION = {version}")
    else:
        print(f"  FAILED VERSION = {version} (expected 0.6.0-alpha15)")
        return 1

    print("\n[4/4] Checking changelog...")
    changelog = pathlib.Path("CHANGELOG.md").read_text(encoding="utf-8")
    if "M6.15" in changelog and "0.6.0-alpha15" in changelog:
        print("  OK CHANGELOG includes M6.15")
    else:
        print("  FAILED CHANGELOG missing M6.15")
        return 1

    print("\n" + "=" * 60)
    print("M6.15 setup complete. Run: python verify_milestone6_15.py")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
