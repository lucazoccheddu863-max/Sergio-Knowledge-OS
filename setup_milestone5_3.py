#!/usr/bin/env python3
"""Setup script for M5.3 — Admin Console."""
from __future__ import annotations

import pathlib
import sys


def main() -> int:
    print("=" * 60)
    print("M5.3 Setup — Admin Console")
    print("=" * 60)

    print("\n[1/4] Checking admin console files...")
    files = [
        "skos/m5/admin_console/__init__.py",
        "skos/m5/admin_console/assets/__init__.py",
        "skos/m5/admin_console/assets/index.html",
        "skos/m5/admin_console/assets/styles.css",
        "skos/m5/admin_console/assets/app.js",
        "tests/m5/test_admin_console.py",
    ]
    for file_path in files:
        if pathlib.Path(file_path).exists():
            print(f"  OK {file_path}")
        else:
            print(f"  MISSING {file_path}")
            return 1

    print("\n[2/4] Checking package assets...")
    from importlib import resources

    html = (
        resources.files("skos.m5.admin_console.assets")
        .joinpath("index.html")
        .read_text(encoding="utf-8")
    )
    if "Sergio Knowledge OS" in html and "/admin/assets/app.js" in html:
        print("  OK admin HTML asset readable")
    else:
        print("  FAILED admin HTML asset incomplete")
        return 1

    print("\n[3/4] Checking version consistency...")
    version = pathlib.Path("VERSION").read_text(encoding="utf-8").strip()
    if version == "0.5.0-alpha3":
        print(f"  OK VERSION = {version}")
    else:
        print(f"  FAILED VERSION = {version} (expected 0.5.0-alpha3)")
        return 1

    print("\n[4/4] Checking changelog...")
    changelog = pathlib.Path("CHANGELOG.md").read_text(encoding="utf-8")
    if "M5.3" in changelog and "0.5.0-alpha3" in changelog:
        print("  OK CHANGELOG includes M5.3")
    else:
        print("  FAILED CHANGELOG missing M5.3")
        return 1

    print("\n" + "=" * 60)
    print("M5.3 setup complete. Run: python verify_milestone5_3.py")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
