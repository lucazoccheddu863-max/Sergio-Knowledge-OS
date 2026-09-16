#!/usr/bin/env python3
"""Setup checks for M7.6 — Local AI Readiness."""
from __future__ import annotations

import pathlib
import sys


def main() -> int:
    files = [
        "skos/m7/runtime/ai_status.py",
        "skos/m7/runtime/application_factory.py",
        "skos/m5/admin_console/assets/index.html",
        "tests/m7/test_ai_service_contract.py",
        "tests/m7/test_application_runtime.py",
        "verify_milestone7_6.py",
    ]
    print("M7.6 Setup — Local AI Readiness")
    for file_path in files:
        if not pathlib.Path(file_path).is_file():
            print(f"MISSING {file_path}")
            return 1
        print(f"OK {file_path}")
    version = pathlib.Path("VERSION").read_text(encoding="utf-8").strip()
    config = pathlib.Path("config.yaml").read_text(encoding="utf-8")
    if version != "0.7.0-alpha6" or "ai_primary_provider: ollama" not in config:
        print("FAILED version or local AI configuration")
        return 1
    print(f"OK VERSION = {version}; local provider = ollama")
    return 0


if __name__ == "__main__":
    sys.exit(main())
