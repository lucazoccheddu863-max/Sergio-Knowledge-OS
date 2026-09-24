#!/usr/bin/env python3
"""Verify M7.10 — Control Room Interface and frozen regressions."""
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
    print("M7.10 Verify — Control Room Interface")
    suites = [
        ("tests/m7/", "27 passed", "M7 tests"),
        ("tests/m6/", "68 passed", "M6 regression"),
        ("tests/m5/", "33 passed", "M5 regression"),
        ("tests/m4/", "240 passed", "M4 regression"),
    ]
    if not all(check_tests(*suite) for suite in suites):
        return 1
    version = pathlib.Path("VERSION").read_text(encoding="utf-8").strip()
    html = pathlib.Path("skos/m5/admin_console/assets/index.html").read_text(encoding="utf-8")
    css = pathlib.Path("skos/m5/admin_console/assets/styles.css").read_text(encoding="utf-8")
    if version != "0.7.0-alpha10" or 'class="sidebar"' not in html or "color-scheme: dark" not in css:
        print("FAILED release metadata or control-room visual wiring")
        return 1
    print("M7.10 verification complete. All checks PASS.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
