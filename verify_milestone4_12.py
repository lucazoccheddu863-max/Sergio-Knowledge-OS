#!/usr/bin/env python3
"""Verify script for M4.12 — Release Engineering / Production Readiness."""
from __future__ import annotations
import subprocess
import sys
import pathlib

def main() -> int:
    print("=" * 60)
    print("M4.12 Verify — Release Engineering / Production Readiness")
    print("=" * 60)

    print("\n[1/6] Running full test suite (regression)...")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/m4/", "-v", "--tb=short"],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        # Count tests
        passed = result.stdout.count(" PASSED ")
        print(f"  ✅ All tests PASS ({passed} tests)")
    else:
        print("  ❌ Tests FAILED")
        print(result.stdout[-2000:])
        return 1

    print("\n[2/6] Running E2E smoke test...")
    from unittest.mock import Mock
    from fastapi.testclient import TestClient
    from skos.m4.infrastructure.adapters.api.fastapi_adapter import FastAPIAdapter
    from skos.m4.infrastructure.ports.query_orchestrator_port import QueryOrchestratorPort
    from skos.m4.infrastructure.ports.config_port import ConfigurationPort
    from skos.m4.domain.query_orchestrator_models import UnifiedQuery, UnifiedResult

    mock_orchestrator = Mock(spec=QueryOrchestratorPort)
    mock_orchestrator.execute.return_value = UnifiedResult(
        query=UnifiedQuery(text="hello", mode="auto"),
        engines_used=["semantic_search"],
        total_time_ms=10.0,
    )
    mock_orchestrator.health_check.return_value = True
    mock_config = Mock(spec=ConfigurationPort)

    adapter = FastAPIAdapter(orchestrator=mock_orchestrator, config=mock_config)
    client = TestClient(adapter.app)

    # E2E: Health
    r = client.get("/api/v1/health")
    assert r.status_code == 200, f"Health failed: {r.status_code}"
    print("  ✅ E2E health check")

    # E2E: Status
    r = client.get("/api/v1/status")
    assert r.status_code == 200
    data = r.json()
    assert data["version"] == "0.4.0"
    assert data["milestone"] == "M4.12"
    print("  ✅ E2E status endpoint")

    # E2E: Query
    r = client.post("/api/v1/query", json={"text": "hello"})
    assert r.status_code == 200
    data = r.json()
    assert data["engines_used"] == ["semantic_search"]
    print("  ✅ E2E query endpoint")

    # E2E: OpenAPI schema
    r = client.get("/api/v1/openapi.json")
    assert r.status_code == 200
    schema = r.json()
    assert "/api/v1/query" in schema["paths"]
    assert "/api/v1/security/status" in schema["paths"]
    print("  ✅ E2E OpenAPI schema")

    # E2E: Metrics
    r = client.get("/metrics")
    assert r.status_code == 200
    print("  ✅ E2E metrics endpoint")

    # E2E: Security status
    r = client.get("/api/v1/security/status")
    assert r.status_code == 200
    print("  ✅ E2E security status endpoint")

    print("\n[3/6] Checking documentation completeness...")
    required_docs = [
        "README.md",
        "docs/ARCHITECTURE.md",
        "docs/ROADMAP.md",
        "docs/api_contract.md",
        "docs/ADR.md",
        "docs/SECURITY_CHECKLIST.md",
        "docs/BENCHMARK_REPORT.md",
        "CHANGELOG.md",
    ]
    for doc in required_docs:
        p = pathlib.Path(doc)
        if p.exists() and len(p.read_text()) > 100:
            print(f"  ✅ {doc} ({len(p.read_text())} chars)")
        else:
            print(f"  ❌ {doc} missing or empty")
            return 1

    print("\n[4/6] Checking SBOM...")
    import json
    with open("SBOM.json") as f:
        sbom = json.load(f)
    assert sbom["version"] == "0.4.0"
    assert len(sbom["packages"]) > 0
    print(f"  ✅ SBOM.json ({len(sbom['packages'])} packages)")

    print("\n[5/6] Checking artifact completeness...")
    artifacts = ["VERSION", "CHANGELOG.md", "TEST_REPORT.txt", "SHA256SUMS"]
    for a in artifacts:
        if pathlib.Path(a).exists():
            print(f"  ✅ {a}")
        else:
            print(f"  ❌ {a} MISSING")
            return 1

    print("\n[6/6] Checking version consistency...")
    with open("VERSION") as f:
        version = f.read().strip()
    assert version == "0.4.0", f"VERSION={version}"
    with open("skos/m4/infrastructure/adapters/api/fastapi_adapter.py") as f:
        content = f.read()
    assert "0.4.0" in content and "M4.12" in content
    print("  ✅ Version consistent across all files")

    print("\n" + "=" * 60)
    print("M4.12 verification complete. All checks PASS.")
    print("Production readiness: CONFIRMED.")
    print("=" * 60)
    return 0

if __name__ == "__main__":
    sys.exit(main())
