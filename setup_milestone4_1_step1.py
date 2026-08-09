#!/usr/bin/env python3
"""Setup script for M4.1 Step 1 — Foundation (DI, Config, Secrets)."""
from __future__ import annotations
import pathlib
import sys

def main() -> int:
    print("=" * 60)
    print("M4.1 Step 1 Setup — Foundation")
    print("=" * 60)

    print("\n[1/3] Checking DI container...")
    if pathlib.Path("skos/m4/di/container.py").exists():
        print("  ✅ DI container")
    else:
        print("  ❌ DI container MISSING")
        return 1

    print("\n[2/3] Checking config adapter...")
    if pathlib.Path("skos/m4/infrastructure/adapters/config/hierarchical_config_adapter.py").exists():
        print("  ✅ Config adapter")
    else:
        print("  ❌ Config adapter MISSING")
        return 1

    print("\n[3/3] Checking secrets adapter...")
    if pathlib.Path("skos/m4/infrastructure/adapters/secrets/env_secret_adapter.py").exists():
        print("  ✅ Secrets adapter")
    else:
        print("  ❌ Secrets adapter MISSING")
        return 1

    print("\n" + "=" * 60)
    print("M4.1 Step 1 setup complete.")
    print("=" * 60)
    return 0

if __name__ == "__main__":
    sys.exit(main())
