#!/usr/bin/env python3
"""Setup script for M4.10 — Observability & Operations Adapter."""
from __future__ import annotations
import pathlib
import sys

def main() -> int:
    print("=" * 60)
    print("M4.10 Setup — Observability & Operations Adapter")
    print("=" * 60)

    print("\n[1/4] Checking observability ports...")
    ports = [
        "skos/m4/infrastructure/ports/metrics_port.py",
        "skos/m4/infrastructure/ports/tracing_port.py",
        "skos/m4/infrastructure/ports/logging_port.py",
    ]
    for p in ports:
        if pathlib.Path(p).exists():
            print(f"    ✅ {p}")
        else:
            print(f"    ❌ {p} MISSING")
            return 1

    print("\n[2/4] Checking observability adapters...")
    adapters = [
        "skos/m4/infrastructure/adapters/observability/__init__.py",
        "skos/m4/infrastructure/adapters/observability/prometheus_adapter.py",
        "skos/m4/infrastructure/adapters/observability/opentelemetry_adapter.py",
        "skos/m4/infrastructure/adapters/observability/structured_logging_adapter.py",
    ]
    for a in adapters:
        if pathlib.Path(a).exists():
            print(f"    ✅ {a}")
        else:
            print(f"    ❌ {a} MISSING")
            return 1

    print("\n[3/4] Checking test file...")
    if pathlib.Path("tests/m4/test_observability.py").exists():
        print("    ✅ tests/m4/test_observability.py")
    else:
        print("    ❌ tests/m4/test_observability.py MISSING")
        return 1

    print("\n[4/4] Checking API contract freeze...")
    with open("skos/m4/infrastructure/adapters/api/fastapi_adapter.py") as f:
        content = f.read()
    if "0.4.0-alpha12" in content and "M4.10" in content:
        print("    ✅ Version and milestone updated")
    else:
        print("    ❌ Version/milestone not updated")
        return 1

    print("\n" + "=" * 60)
    print("M4.10 setup complete. Run: python verify_milestone4_10.py")
    print("=" * 60)
    return 0

if __name__ == "__main__":
    sys.exit(main())
