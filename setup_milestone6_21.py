#!/usr/bin/env python3
"""Setup script for M6.21 — Local Operator CLI."""
from __future__ import annotations

import pathlib
import sys


def main() -> int:
    print("=" * 60)
    print("M6.21 Setup — Local Operator CLI")
    print("=" * 60)

    print("\n[1/4] Checking operator CLI files...")
    files = [
        "skos/m6/production/operator_cli.py",
        "tests/m6/test_operator_cli.py",
        "pyproject.toml",
    ]
    for file_path in files:
        if pathlib.Path(file_path).exists():
            print(f"  OK {file_path}")
        else:
            print(f"  MISSING {file_path}")
            return 1

    print("\n[2/4] Checking operator command wiring...")
    cli_text = pathlib.Path("skos/m6/production/operator_cli.py").read_text(encoding="utf-8")
    project_text = pathlib.Path("pyproject.toml").read_text(encoding="utf-8")
    commands = ("prepare", "status", "report", "start")
    if all(f'"{command}"' in cli_text for command in commands) and "sergio-knowledge =" in project_text:
        print("  OK operator CLI wiring available")
    else:
        print("  FAILED operator CLI wiring missing")
        return 1

    print("\n[3/4] Checking version consistency...")
    version = pathlib.Path("VERSION").read_text(encoding="utf-8").strip()
    if version == "0.6.0-alpha21":
        print(f"  OK VERSION = {version}")
    else:
        print(f"  FAILED VERSION = {version} (expected 0.6.0-alpha21)")
        return 1

    print("\n[4/4] Checking changelog...")
    changelog = pathlib.Path("CHANGELOG.md").read_text(encoding="utf-8")
    if "M6.21" in changelog and "0.6.0-alpha21" in changelog:
        print("  OK CHANGELOG includes M6.21")
    else:
        print("  FAILED CHANGELOG missing M6.21")
        return 1

    print("\n" + "=" * 60)
    print("M6.21 setup complete. Run: python verify_milestone6_21.py")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
