#!/usr/bin/env python3
"""Setup checks for M7.11 — Local Database Bootstrap."""
from __future__ import annotations

import pathlib
import sys


def main() -> int:
    files = [
        "schema_v1.sql",
        "skos/m6/production/launch.py",
        "tests/m6/test_local_launch.py",
        "tests/m6/test_operator_cli.py",
        "verify_milestone7_11.py",
    ]
    print("M7.11 Setup — Local Database Bootstrap")
    for file_path in files:
        if not pathlib.Path(file_path).is_file():
            print(f"MISSING {file_path}")
            return 1
        print(f"OK {file_path}")
    version = pathlib.Path("VERSION").read_text(encoding="utf-8").strip()
    if version != "0.7.0-alpha11":
        print(f"FAILED VERSION = {version}")
        return 1
    print(f"OK VERSION = {version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
