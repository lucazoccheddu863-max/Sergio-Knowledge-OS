#!/usr/bin/env python3
"""Setup script for M6.2 — Admin Readiness."""
from __future__ import annotations

import pathlib
import sys


def main() -> int:
    print("=" * 60)
    print("M6.2 Setup — Admin Readiness")
    print("=" * 60)

    print("\n[1/4] Checking M6.2 files...")
    files = [
        "skos/m4/infrastructure/adapters/api/fastapi_adapter.py",
        "skos/m5/admin_console/assets/index.html",
        "skos/m5/admin_console/assets/app.js",
        "tests/m6/test_admin_readiness_api.py",
    ]
    for file_path in files:
        if pathlib.Path(file_path).exists():
            print(f"  OK {file_path}")
        else:
            print(f"  MISSING {file_path}")
            return 1

    print("\n[2/4] Checking readiness endpoint wiring...")
    api_text = pathlib.Path("skos/m4/infrastructure/adapters/api/fastapi_adapter.py").read_text(
        encoding="utf-8"
    )
    js_text = pathlib.Path("skos/m5/admin_console/assets/app.js").read_text(encoding="utf-8")
    html_text = pathlib.Path("skos/m5/admin_console/assets/index.html").read_text(encoding="utf-8")
    if "/api/v1/admin/readiness" in api_text and "/api/v1/admin/readiness" in js_text and "Production Readiness" in html_text:
        print("  OK readiness endpoint and console panel")
    else:
        print("  FAILED readiness endpoint or console panel missing")
        return 1

    print("\n[3/4] Checking version consistency...")
    version = pathlib.Path("VERSION").read_text(encoding="utf-8").strip()
    if version == "0.6.0-alpha2":
        print(f"  OK VERSION = {version}")
    else:
        print(f"  FAILED VERSION = {version} (expected 0.6.0-alpha2)")
        return 1

    print("\n[4/4] Checking changelog...")
    changelog = pathlib.Path("CHANGELOG.md").read_text(encoding="utf-8")
    if "M6.2" in changelog and "0.6.0-alpha2" in changelog:
        print("  OK CHANGELOG includes M6.2")
    else:
        print("  FAILED CHANGELOG missing M6.2")
        return 1

    print("\n" + "=" * 60)
    print("M6.2 setup complete. Run: python verify_milestone6_2.py")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
