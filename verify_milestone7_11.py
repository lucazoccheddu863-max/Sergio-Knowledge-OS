#!/usr/bin/env python3
"""Verify M7.11 — Local Database Bootstrap and frozen regressions."""
from __future__ import annotations

import pathlib
import sqlite3
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
    print("M7.11 Verify — Local Database Bootstrap")
    suites = [
        ("tests/m7/", "27 passed", "M7 tests"),
        ("tests/m6/", "71 passed", "M6 regression"),
        ("tests/m5/", "33 passed", "M5 regression"),
        ("tests/m4/", "240 passed", "M4 regression"),
    ]
    if not all(check_tests(*suite) for suite in suites):
        return 1
    version = pathlib.Path("VERSION").read_text(encoding="utf-8").strip()
    database = pathlib.Path("data/sergio_knowledge.db")
    if version != "0.7.0-alpha11" or not database.is_file():
        print("FAILED release metadata or local database")
        return 1
    with sqlite3.connect(database) as connection:
        schema_version = connection.execute(
            "SELECT value FROM schema_meta WHERE key = 'schema_version'"
        ).fetchone()
    if schema_version != ("1",):
        print("FAILED local database schema version")
        return 1
    print("M7.11 verification complete. All checks PASS.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
