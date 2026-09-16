#!/usr/bin/env python3
"""Setup script for M7.2 — Complete Application Runtime Assembly."""
from __future__ import annotations

import pathlib
import sys


def main() -> int:
    print("=" * 60)
    print("M7.2 Setup — Complete Application Runtime Assembly")
    print("=" * 60)

    files = [
        "skos/m7/runtime/application_factory.py",
        "skos/m6/production/local_server.py",
        "tests/m7/test_application_runtime.py",
        "pyproject.toml",
    ]
    print("\n[1/4] Checking runtime assembly files...")
    for file_path in files:
        if pathlib.Path(file_path).exists():
            print(f"  OK {file_path}")
        else:
            print(f"  MISSING {file_path}")
            return 1

    print("\n[2/4] Checking runtime factory wiring...")
    factory = pathlib.Path("skos/m7/runtime/application_factory.py").read_text(encoding="utf-8")
    server = pathlib.Path("skos/m6/production/local_server.py").read_text(encoding="utf-8")
    required = ("AIService", "SemanticSearchService", "RAGPipelineService", "QueryOrchestratorService")
    if all(name in factory for name in required) and "build_application_runtime" in server:
        print("  OK complete runtime factory available")
    else:
        print("  FAILED runtime factory wiring missing")
        return 1

    print("\n[3/4] Checking version consistency...")
    version = pathlib.Path("VERSION").read_text(encoding="utf-8").strip()
    if version == "0.7.0-alpha2":
        print(f"  OK VERSION = {version}")
    else:
        print(f"  FAILED VERSION = {version} (expected 0.7.0-alpha2)")
        return 1

    print("\n[4/4] Checking changelog...")
    changelog = pathlib.Path("CHANGELOG.md").read_text(encoding="utf-8")
    if "M7.2" in changelog and "0.7.0-alpha2" in changelog:
        print("  OK CHANGELOG includes M7.2")
    else:
        print("  FAILED CHANGELOG missing M7.2")
        return 1

    print("\n" + "=" * 60)
    print("M7.2 setup complete. Run: python verify_milestone7_2.py")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
