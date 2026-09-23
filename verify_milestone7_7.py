#!/usr/bin/env python3
"""Verify M7.7 — Local Beta Reliability and frozen regressions."""
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
    print("M7.7 Verify — Local Beta Reliability")
    suites = [
        ("tests/m7/", "20 passed", "M7 tests"),
        ("tests/m6/", "67 passed", "M6 regression"),
        ("tests/m5/", "32 passed", "M5 regression"),
        ("tests/m4/", "238 passed", "M4 regression"),
    ]
    if not all(check_tests(*suite) for suite in suites):
        return 1
    version = pathlib.Path("VERSION").read_text(encoding="utf-8").strip()
    config = pathlib.Path("config.yaml").read_text(encoding="utf-8")
    api = pathlib.Path("skos/m4/infrastructure/adapters/api/fastapi_adapter.py").read_text(
        encoding="utf-8"
    )
    adr = pathlib.Path("docs/ADR.md").read_text(encoding="utf-8")
    if (
        version != "0.7.0-alpha7"
        or "timeout: 300" not in config
        or "runtime.version" not in api
        or "ADR-007" not in adr
    ):
        print("FAILED release metadata, local beta wiring or integration ADR")
        return 1
    print("M7.7 verification complete. All checks PASS.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
