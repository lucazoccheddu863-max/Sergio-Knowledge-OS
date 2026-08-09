#!/usr/bin/env python3
"""Setup script for M4.11 — Security & Auth."""
from __future__ import annotations
import pathlib
import sys

def main() -> int:
    print("=" * 60)
    print("M4.11 Setup — Security & Auth")
    print("=" * 60)

    print("\n[1/5] Checking security ports...")
    ports = [
        "skos/m4/infrastructure/ports/auth_port.py",
        "skos/m4/infrastructure/ports/authorization_port.py",
        "skos/m4/infrastructure/ports/rate_limit_port.py",
        "skos/m4/infrastructure/ports/audit_port.py",
    ]
    for p in ports:
        if pathlib.Path(p).exists():
            print(f"  ✅ {p}")
        else:
            print(f"  ❌ {p} MISSING")
            return 1

    print("\n[2/5] Checking security adapters...")
    adapters = [
        "skos/m4/infrastructure/adapters/security/__init__.py",
        "skos/m4/infrastructure/adapters/security/api_key_auth_adapter.py",
        "skos/m4/infrastructure/adapters/security/rbac_authorization_adapter.py",
        "skos/m4/infrastructure/adapters/security/inmemory_rate_limit_adapter.py",
        "skos/m4/infrastructure/adapters/security/structured_audit_adapter.py",
    ]
    for a in adapters:
        if pathlib.Path(a).exists():
            print(f"  ✅ {a}")
        else:
            print(f"  ❌ {a} MISSING")
            return 1

    print("\n[3/5] Checking test file...")
    if pathlib.Path("tests/m4/test_security.py").exists():
        print("  ✅ tests/m4/test_security.py")
    else:
        print("  ❌ tests/m4/test_security.py MISSING")
        return 1

    print("\n[4/5] Checking API integration...")
    with open("skos/m4/infrastructure/adapters/api/fastapi_adapter.py") as f:
        content = f.read()
    if "0.4.0-alpha13" in content and "M4.11" in content:
        print("  ✅ Version and milestone updated")
    else:
        print("  ❌ Version/milestone not updated")
        return 1
    if "security" in content and "auth" in content:
        print("  ✅ Security integration present")
    else:
        print("  ❌ Security integration missing")
        return 1

    print("\n[5/5] Checking DTO updates...")
    with open("skos/m4/infrastructure/adapters/api/dto.py") as f:
        content = f.read()
    if "SecurityStatusResponse" in content:
        print("  ✅ SecurityStatusResponse DTO present")
    else:
        print("  ❌ SecurityStatusResponse DTO missing")
        return 1

    print("\n" + "=" * 60)
    print("M4.11 setup complete. Run: python verify_milestone4_11.py")
    print("=" * 60)
    return 0

if __name__ == "__main__":
    sys.exit(main())
