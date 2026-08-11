#!/usr/bin/env python3
"""Setup script for M5.1 — Persistence Layer."""
from __future__ import annotations
import pathlib
import sys

def main() -> int:
    print("=" * 60)
    print("M5.1 Setup — Persistence Layer")
    print("=" * 60)

    print("\n[1/5] Checking persistence adapters...")
    adapters = [
        "skos/m5/infrastructure/adapters/persistence/redis_eventbus_adapter.py",
        "skos/m5/infrastructure/adapters/persistence/redis_rate_limit_adapter.py",
        "skos/m5/infrastructure/adapters/persistence/postgresql_audit_adapter.py",
        "skos/m5/infrastructure/adapters/persistence/postgresql_auth_adapter.py",
        "skos/m5/infrastructure/adapters/persistence/postgresql_kg_adapter.py",
    ]
    for a in adapters:
        if pathlib.Path(a).exists():
            print(f"  ✅ {a}")
        else:
            print(f"  ❌ {a} MISSING")
            return 1

    print("\n[2/5] Checking port compliance...")
    from skos.m5.infrastructure.adapters.persistence.redis_eventbus_adapter import RedisEventBusAdapter
    from skos.m5.infrastructure.adapters.persistence.redis_rate_limit_adapter import RedisRateLimitAdapter
    from skos.m5.infrastructure.adapters.persistence.postgresql_audit_adapter import PostgreSQLAuditAdapter
    from skos.m5.infrastructure.adapters.persistence.postgresql_auth_adapter import PostgreSQLAuthAdapter
    from skos.m5.infrastructure.adapters.persistence.postgresql_kg_adapter import PostgreSQLKnowledgeGraphAdapter
    from skos.m4.infrastructure.ports.event_bus_port import EventBusPort
    from skos.m4.infrastructure.ports.rate_limit_port import RateLimitPort
    from skos.m4.infrastructure.ports.audit_port import AuditPort
    from skos.m4.infrastructure.ports.auth_port import AuthPort
    from skos.m4.infrastructure.ports.knowledge_graph_port import KnowledgeGraphPort

    checks = [
        (issubclass(RedisEventBusAdapter, EventBusPort), "RedisEventBusAdapter -> EventBusPort"),
        (issubclass(RedisRateLimitAdapter, RateLimitPort), "RedisRateLimitAdapter -> RateLimitPort"),
        (issubclass(PostgreSQLAuditAdapter, AuditPort), "PostgreSQLAuditAdapter -> AuditPort"),
        (issubclass(PostgreSQLAuthAdapter, AuthPort), "PostgreSQLAuthAdapter -> AuthPort"),
        (issubclass(PostgreSQLKnowledgeGraphAdapter, KnowledgeGraphPort), "PostgreSQLKnowledgeGraphAdapter -> KnowledgeGraphPort"),
    ]
    for ok, name in checks:
        if ok:
            print(f"  ✅ {name}")
        else:
            print(f"  ❌ {name}")
            return 1

    print("\n[3/5] Checking test file...")
    if pathlib.Path("tests/m5/test_persistence.py").exists():
        print("  ✅ tests/m5/test_persistence.py")
    else:
        print("  ❌ tests/m5/test_persistence.py MISSING")
        return 1

    print("\n[4/5] Checking dependencies...")
    try:
        import redis
        print("  ✅ redis")
    except ImportError:
        print("  ❌ redis not installed")
        return 1
    try:
        import psycopg2
        print("  ✅ psycopg2")
    except ImportError:
        print("  ❌ psycopg2 not installed")
        return 1

    print("\n[5/5] Checking version consistency...")
    with open("VERSION") as f:
        v = f.read().strip()
    if v == "0.5.0-alpha1":
        print(f"  ✅ VERSION = {v} (M5.1 milestone)")
    else:
        print(f"  ❌ VERSION = {v} (expected 0.5.0-alpha1)")
        return 1

    print("\n" + "=" * 60)
    print("M5.1 setup complete. Run: python verify_milestone5_1.py")
    print("=" * 60)
    return 0

if __name__ == "__main__":
    sys.exit(main())
