#!/usr/bin/env python3
"""Setup checks for M7.5 — Ask Sergio Console."""
from __future__ import annotations

import pathlib
import sys


def main() -> int:
    files = [
        "skos/m5/admin_console/assets/index.html",
        "skos/m5/admin_console/assets/app.js",
        "skos/m5/admin_console/assets/styles.css",
        "tests/m5/test_admin_console.py",
        "tests/m7/test_application_runtime.py",
        "verify_milestone7_5.py",
    ]
    print("M7.5 Setup — Ask Sergio Console")
    for file_path in files:
        if not pathlib.Path(file_path).is_file():
            print(f"MISSING {file_path}")
            return 1
        print(f"OK {file_path}")
    version = pathlib.Path("VERSION").read_text(encoding="utf-8").strip()
    if version != "0.7.0-alpha5":
        print(f"FAILED VERSION = {version}")
        return 1
    print(f"OK VERSION = {version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
