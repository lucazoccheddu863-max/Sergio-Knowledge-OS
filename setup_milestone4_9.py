#!/usr/bin/env python3
"""Setup script for M4.9 — REST API Adapter."""
from __future__ import annotations

import sys


def main() -> int:
    print("=" * 60)
    print("M4.9 Setup — REST API Adapter")
    print("=" * 60)

    print("\n[1/3] Checking FastAPI dependency...")
    try:
        import fastapi
        print(f"    ✅ FastAPI {fastapi.__version__} found")
    except ImportError:
        print("    ❌ FastAPI not found. Install with: pip install fastapi uvicorn")
        return 1

    print("\n[2/3] Checking test dependencies...")
    try:
        import httpx
        print("    ✅ httpx found (required by TestClient)")
    except ImportError:
        print("    ❌ httpx not found. Install with: pip install httpx")
        return 1

    print("\n[3/3] Verifying adapter files...")
    expected_files = [
        "skos/m4/infrastructure/adapters/api/__init__.py",
        "skos/m4/infrastructure/adapters/api/dto.py",
        "skos/m4/infrastructure/adapters/api/fastapi_adapter.py",
        "tests/m4/test_api_adapter.py",
    ]
    import pathlib
    all_ok = True
    for f in expected_files:
        path = pathlib.Path(f)
        if path.exists():
            print(f"    ✅ {f}")
        else:
            print(f"    ❌ {f} MISSING")
            all_ok = False

    if not all_ok:
        return 1

    print("\n" + "=" * 60)
    print("M4.9 setup complete. Run: python verify_milestone4_9.py")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
