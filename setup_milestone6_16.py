#!/usr/bin/env python3
"""Setup script for M6.16 — Operator Manual."""
from __future__ import annotations

import pathlib
import sys


def main() -> int:
    print("=" * 60)
    print("M6.16 Setup — Operator Manual")
    print("=" * 60)

    print("\n[1/4] Checking operator manual files...")
    files = [
        "skos/m6/production/manual.py",
        "tests/m6/test_operator_manual.py",
        "skos/m5/admin_console/assets/index.html",
        "skos/m5/admin_console/assets/app.js",
    ]
    for file_path in files:
        if pathlib.Path(file_path).exists():
            print(f"  OK {file_path}")
        else:
            print(f"  MISSING {file_path}")
            return 1

    print("\n[2/4] Checking operator manual wiring...")
    api_text = pathlib.Path("skos/m4/infrastructure/adapters/api/fastapi_adapter.py").read_text(
        encoding="utf-8"
    )
    js_text = pathlib.Path("skos/m5/admin_console/assets/app.js").read_text(encoding="utf-8")
    route = "/api/v1/admin/manual"
    if route in api_text and route in js_text:
        print("  OK operator manual endpoint available")
    else:
        print("  FAILED operator manual endpoint missing")
        return 1

    print("\n[3/4] Checking version consistency...")
    version = pathlib.Path("VERSION").read_text(encoding="utf-8").strip()
    if version == "0.6.0-alpha16":
        print(f"  OK VERSION = {version}")
    else:
        print(f"  FAILED VERSION = {version} (expected 0.6.0-alpha16)")
        return 1

    print("\n[4/4] Checking changelog...")
    changelog = pathlib.Path("CHANGELOG.md").read_text(encoding="utf-8")
    if "M6.16" in changelog and "0.6.0-alpha16" in changelog:
        print("  OK CHANGELOG includes M6.16")
    else:
        print("  FAILED CHANGELOG missing M6.16")
        return 1

    print("\n" + "=" * 60)
    print("M6.16 setup complete. Run: python verify_milestone6_16.py")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
