#!/usr/bin/env python3
"""Setup script for M5.2 — Runtime Wiring."""
from __future__ import annotations

import pathlib
import sys


def main() -> int:
    print("=" * 60)
    print("M5.2 Setup — Runtime Wiring")
    print("=" * 60)

    print("\n[1/4] Checking runtime files...")
    files = [
        "skos/m5/runtime/__init__.py",
        "skos/m5/runtime/persistence_factory.py",
        "tests/m5/test_runtime_wiring.py",
    ]
    for file_path in files:
        if pathlib.Path(file_path).exists():
            print(f"  OK {file_path}")
        else:
            print(f"  MISSING {file_path}")
            return 1

    print("\n[2/4] Checking runtime import...")
    from skos.m5.runtime import build_persistence_runtime
    from skos.m4.infrastructure.adapters.config.hierarchical_config_adapter import (
        HierarchicalConfigAdapter,
    )

    runtime = build_persistence_runtime(
        HierarchicalConfigAdapter(defaults={"m5": {"persistence": {"mode": "memory"}}})
    )
    if runtime.health().healthy:
        print("  OK memory runtime healthy")
    else:
        print("  FAILED memory runtime unhealthy")
        return 1

    print("\n[3/4] Checking version consistency...")
    version = pathlib.Path("VERSION").read_text(encoding="utf-8").strip()
    if version == "0.5.0-alpha2":
        print(f"  OK VERSION = {version}")
    else:
        print(f"  FAILED VERSION = {version} (expected 0.5.0-alpha2)")
        return 1

    print("\n[4/4] Checking config file...")
    content = pathlib.Path("config.yaml").read_text(encoding="utf-8")
    if "m5:" in content and "persistence:" in content and "mode: memory" in content:
        print("  OK config.yaml includes M5 runtime keys")
    else:
        print("  FAILED config.yaml missing M5 runtime keys")
        return 1

    print("\n" + "=" * 60)
    print("M5.2 setup complete. Run: python verify_milestone5_2.py")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
