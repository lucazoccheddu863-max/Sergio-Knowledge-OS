#!/usr/bin/env python3
"""Setup checks for M7.8 — One-command Local Start."""
from __future__ import annotations

import pathlib
import sys


def main() -> int:
    files = [
        "skos/m7/runtime/local_ai_process.py",
        "skos/m6/production/operator_cli.py",
        "tests/m7/test_local_ai_process.py",
        "tests/m6/test_operator_cli.py",
        "verify_milestone7_8.py",
    ]
    print("M7.8 Setup — One-command Local Start")
    for file_path in files:
        if not pathlib.Path(file_path).is_file():
            print(f"MISSING {file_path}")
            return 1
        print(f"OK {file_path}")
    version = pathlib.Path("VERSION").read_text(encoding="utf-8").strip()
    if version != "0.7.0-alpha8":
        print(f"FAILED VERSION = {version}")
        return 1
    print(f"OK VERSION = {version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
