#!/usr/bin/env python3
"""Setup checks for M7.7 — Local Beta Reliability."""
from __future__ import annotations

import pathlib
import sys


def main() -> int:
    files = [
        "skos/m4/infrastructure/adapters/api/fastapi_adapter.py",
        "skos/m7/runtime/application_factory.py",
        "tests/m7/test_application_runtime.py",
        "docs/ADR.md",
        "verify_milestone7_7.py",
    ]
    print("M7.7 Setup — Local Beta Reliability")
    for file_path in files:
        if not pathlib.Path(file_path).is_file():
            print(f"MISSING {file_path}")
            return 1
        print(f"OK {file_path}")
    version = pathlib.Path("VERSION").read_text(encoding="utf-8").strip()
    config = pathlib.Path("config.yaml").read_text(encoding="utf-8")
    adr = pathlib.Path("docs/ADR.md").read_text(encoding="utf-8")
    if version != "0.7.0-alpha7" or "timeout: 300" not in config or "ADR-007" not in adr:
        print("FAILED version, local timeout or integration ADR")
        return 1
    print(f"OK VERSION = {version}; local timeout = 300 seconds; ADR-007 present")
    return 0


if __name__ == "__main__":
    sys.exit(main())
