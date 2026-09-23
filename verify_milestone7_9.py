#!/usr/bin/env python3
"""Verify M7.9 — Grounded Local Retrieval and frozen regressions."""
from __future__ import annotations

import pathlib
import subprocess
import sys


def check_tests(path: str, expected: str, label: str) -> bool:
    result = subprocess.run([sys.executable, "-m", "pytest", path, "-q"], capture_output=True, text=True)
    if result.returncode == 0 and expected in result.stdout:
        print(f"OK {label} ({expected})")
        return True
    print(f"FAILED {label}\n{result.stdout[-1200:]}\n{result.stderr[-1200:]}")
    return False


def main() -> int:
    print("M7.9 Verify — Grounded Local Retrieval")
    suites = [
        ("tests/m7/", "27 passed", "M7 tests"),
        ("tests/m6/", "68 passed", "M6 regression"),
        ("tests/m5/", "32 passed", "M5 regression"),
        ("tests/m4/", "240 passed", "M4 regression"),
    ]
    if not all(check_tests(*suite) for suite in suites):
        return 1
    version = pathlib.Path("VERSION").read_text(encoding="utf-8").strip()
    config = pathlib.Path("config.yaml").read_text(encoding="utf-8")
    if (
        version != "0.7.0-alpha9"
        or 'collection_name: "semantic_search_m7_9"' not in config
        or 'document_prefix: "search_document: "' not in config
        or 'query_prefix: "search_query: "' not in config
    ):
        print("FAILED release metadata or grounded retrieval configuration")
        return 1
    print("M7.9 verification complete. All checks PASS.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
