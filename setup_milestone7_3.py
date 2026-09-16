#!/usr/bin/env python3
"""Setup checks for M7.3 — Safe Document Import."""
from __future__ import annotations

import pathlib
import sys


def main() -> int:
    print("=" * 60)
    print("M7.3 Setup — Safe Document Import")
    print("=" * 60)
    files = [
        "skos/m7/runtime/document_import.py",
        "skos/m7/runtime/application_factory.py",
        "tests/m7/test_document_import.py",
        "verify_milestone7_3.py",
    ]
    for file_path in files:
        if not pathlib.Path(file_path).is_file():
            print(f"MISSING {file_path}")
            return 1
        print(f"OK {file_path}")

    version = pathlib.Path("VERSION").read_text(encoding="utf-8").strip()
    if version != "0.7.0-alpha3":
        print(f"FAILED VERSION = {version}")
        return 1
    print(f"OK VERSION = {version}")
    print("M7.3 setup complete. Run: python verify_milestone7_3.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
