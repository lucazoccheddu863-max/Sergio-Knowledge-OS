#!/usr/bin/env python3
"""Verify M7.8 — One-command Local Start and frozen regressions."""
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
    print("M7.8 Verify — One-command Local Start")
    suites = [
        ("tests/m7/", "23 passed", "M7 tests"),
        ("tests/m6/", "68 passed", "M6 regression"),
        ("tests/m5/", "32 passed", "M5 regression"),
        ("tests/m4/", "238 passed", "M4 regression"),
    ]
    if not all(check_tests(*suite) for suite in suites):
        return 1
    version = pathlib.Path("VERSION").read_text(encoding="utf-8").strip()
    startup = pathlib.Path("skos/m7/runtime/local_ai_process.py").read_text(encoding="utf-8")
    cli = pathlib.Path("skos/m6/production/operator_cli.py").read_text(encoding="utf-8")
    if version != "0.7.0-alpha8" or "ensure_ollama_running" not in startup or "_ensure_local_ai" not in cli:
        print("FAILED release metadata or one-command startup wiring")
        return 1
    print("M7.8 verification complete. All checks PASS.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
