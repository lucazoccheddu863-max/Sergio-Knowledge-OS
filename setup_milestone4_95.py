#!/usr/bin/env python3
"""Setup script for M4.9.5 — API Contract Freeze."""
from __future__ import annotations

import pathlib
import sys


def main() -> int:
    print("=" * 60)
    print("M4.9.5 Setup — API Contract Freeze")
    print("=" * 60)

    print("\n[1/4] Checking FastAPI dependency...")
    try:
        import fastapi
        print(f"    ✅ FastAPI {fastapi.__version__} found")
    except ImportError:
        print("    ❌ FastAPI not found")
        return 1

    print("\n[2/4] Checking test dependencies...")
    try:
        import httpx
        print("    ✅ httpx found")
    except ImportError:
        print("    ❌ httpx not found")
        return 1

    print("\n[3/4] Verifying adapter files...")
    expected_files = [
        "skos/m4/infrastructure/adapters/api/__init__.py",
        "skos/m4/infrastructure/adapters/api/dto.py",
        "skos/m4/infrastructure/adapters/api/fastapi_adapter.py",
        "tests/m4/test_api_adapter.py",
        "docs/api_contract.md",
    ]
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

    print("\n[4/4] Verifying API contract documentation...")
    contract_path = pathlib.Path("docs/api_contract.md")
    content = contract_path.read_text()
    checks = [
        ("API Contract v1" in content, "API Contract v1 header"),
        ("M4.9.5" in content, "Milestone reference"),
        ("/api/v1/query" in content, "Query endpoint documented"),
        ("/api/v1/admin" in content, "Admin routes documented"),
        ("APIError" in content, "Error model documented"),
    ]
    for ok, desc in checks:
        if ok:
            print(f"    ✅ {desc}")
        else:
            print(f"    ❌ {desc} MISSING")
            all_ok = False
    if not all_ok:
        return 1

    print("\n" + "=" * 60)
    print("M4.9.5 setup complete. Run: python verify_milestone4_95.py")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
