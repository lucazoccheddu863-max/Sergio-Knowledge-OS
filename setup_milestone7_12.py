#!/usr/bin/env python3
"""Setup checks for M7.12 - Design System Foundation."""
from __future__ import annotations

import pathlib
import sys


def main() -> int:
    files = [
        "skos/m5/admin_console/assets/index.html",
        "skos/m5/admin_console/assets/styles.css",
        "skos/m5/admin_console/assets/app.js",
        "tests/m5/test_admin_console.py",
        "tests/m6/test_admin_readiness_api.py",
        "verify_milestone7_12.py",
    ]
    print("M7.12 Setup - Design System Foundation")
    for file_path in files:
        if not pathlib.Path(file_path).is_file():
            print(f"MISSING {file_path}")
            return 1
        print(f"OK {file_path}")
    version = pathlib.Path("VERSION").read_text(encoding="utf-8").strip()
    if version != "0.7.0-alpha12":
        print(f"FAILED VERSION = {version}")
        return 1
    print(f"OK VERSION = {version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
