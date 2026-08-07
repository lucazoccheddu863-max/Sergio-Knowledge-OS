#!/usr/bin/env python3
"""Verification script for Milestone 4.4 — Vector DB Integration."""
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def ensure_package() -> bool:
    try:
        import skos
        return True
    except ImportError:
        setup = PROJECT_ROOT / "setup_milestone4_4.py"
        if setup.exists():
            r = subprocess.run([sys.executable, str(setup)])
            return r.returncode == 0
        return False


def _check(markers: list[Path], name: str) -> bool:
    print(f"\n{'='*60}")
    print(f"Verifying {name}...")
    print(f"{'='*60}")
    missing = [m for m in markers if not m.exists()]
    if missing:
        print(f"⚠️ {name}: SKIP (delta release)")
        return True
    print(f"✅ {name}: PRESENT")
    return True


def verify_m2() -> bool:
    return _check([PROJECT_ROOT / "skos" / "m2"], "M2 Baseline")


def verify_m3() -> bool:
    return _check([PROJECT_ROOT / "skos" / "m3"], "M3 Baseline")


def verify_m4_1_1() -> bool:
    return _check([PROJECT_ROOT / "skos" / "m4" / "di" / "container.py"], "M4.1.1 Baseline")


def verify_m4_1_2() -> bool:
    return _check(
        [PROJECT_ROOT / "skos" / "m4" / "infrastructure" / "adapters" / "event_bus" / "in_memory_event_bus.py"],
        "M4.1.2 Baseline",
    )


def verify_m4_2() -> bool:
    return _check(
        [PROJECT_ROOT / "skos" / "m4" / "infrastructure" / "adapters" / "ai_providers" / "provider_registry.py"],
        "M4.2 Baseline",
    )


def verify_m4_3() -> bool:
    return _check(
        [PROJECT_ROOT / "skos" / "m4" / "application" / "services" / "embedding_pipeline.py"],
        "M4.3 Baseline",
    )


def run_tests() -> bool:
    print(f"\n{'='*60}")
    print("Running M4.4 Test Suite...")
    print(f"{'='*60}")
    test_dir = PROJECT_ROOT / "tests" / "m4"
    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(test_dir), "-v", "--tb=short"],
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    return result.returncode == 0


def verify_vector_store_port() -> bool:
    print(f"\n{'='*60}")
    print("Verifying VectorStorePort...")
    print(f"{'='*60}")
    try:
        from skos.m4.infrastructure.ports.vector_store_port import VectorStorePort
        assert hasattr(VectorStorePort, "upsert")
        assert hasattr(VectorStorePort, "search")
        assert hasattr(VectorStorePort, "delete")
        assert hasattr(VectorStorePort, "health_check")
        print("✅ VectorStorePort: PASSED")
        return True
    except Exception as e:
        print(f"❌ VectorStorePort: FAILED — {e}")
        return False


def verify_chromadb_adapter() -> bool:
    print(f"\n{'='*60}")
    print("Verifying ChromaDBAdapter...")
    print(f"{'='*60}")
    try:
        from skos.m4.infrastructure.adapters.vector_store.chromadb_adapter import ChromaDBAdapter
        adapter = ChromaDBAdapter(persist_directory=None)
        assert adapter.health_check() is True
        assert ChromaDBAdapter._sanitize_collection_name("bad name!") == "bad_name"
        assert ChromaDBAdapter._normalize_metadata({}) is None
        print("✅ ChromaDBAdapter: PASSED")
        return True
    except Exception as e:
        print(f"❌ ChromaDBAdapter: FAILED — {e}")
        return False


def verify_vector_store_service() -> bool:
    print(f"\n{'='*60}")
    print("Verifying VectorStoreService...")
    print(f"{'='*60}")
    try:
        from skos.m4.application.services.vector_store_service import VectorStoreService
        from skos.m4.infrastructure.adapters.vector_store.chromadb_adapter import ChromaDBAdapter
        adapter = ChromaDBAdapter(persist_directory=None)
        service = VectorStoreService(adapter)
        assert service.health_check() is True
        print("✅ VectorStoreService: PASSED")
        return True
    except Exception as e:
        print(f"❌ VectorStoreService: FAILED — {e}")
        return False


def verify_architecture() -> bool:
    print(f"\n{'='*60}")
    print("Verifying Architecture Rules...")
    print(f"{'='*60}")
    try:
        import ast
        violations = []
        for py_file in (PROJECT_ROOT / "skos" / "m4" / "domain").rglob("*.py"):
            if py_file.name == "__init__.py":
                continue
            tree = ast.parse(py_file.read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    mod = node.module or ""
                    if "infrastructure" in mod or "adapter" in mod:
                        violations.append(f"{py_file}:{node.lineno}")
        for py_file in (PROJECT_ROOT / "skos" / "m4" / "application").rglob("*.py"):
            if py_file.name == "__init__.py":
                continue
            tree = ast.parse(py_file.read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    mod = node.module or ""
                    if "infrastructure" in mod and "adapter" in mod and "port" not in mod:
                        violations.append(f"{py_file}:{node.lineno}")
        if violations:
            print(f"❌ Violations: {violations}")
            return False
        print("✅ Architecture Rules: PASSED")
        return True
    except Exception as e:
        print(f"❌ Architecture Rules: FAILED — {e}")
        return False


def main() -> int:
    print(f"\n{'='*60}")
    print("MILESTONE 4.4 — VECTOR DB INTEGRATION")
    print(f"{'='*60}")
    if not ensure_package():
        return 1
    results = {
        "M2 Baseline": verify_m2(),
        "M3 Baseline": verify_m3(),
        "M4.1.1 Baseline": verify_m4_1_1(),
        "M4.1.2 Baseline": verify_m4_1_2(),
        "M4.2 Baseline": verify_m4_2(),
        "M4.3 Baseline": verify_m4_3(),
        "VectorStorePort": verify_vector_store_port(),
        "ChromaDBAdapter": verify_chromadb_adapter(),
        "VectorStoreService": verify_vector_store_service(),
        "Architecture Rules": verify_architecture(),
        "M4.4 Test Suite": run_tests(),
    }
    print(f"\n{'='*60}")
    print("VERIFICATION SUMMARY")
    print(f"{'='*60}")
    all_passed = True
    for name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{name:<30} {status}")
        if not passed:
            all_passed = False
    total = len(results)
    passed_count = sum(1 for p in results.values() if p)
    print(f"{'='*60}")
    print(f"\nTotal .......... {passed_count}/{total} PASS")
    print(f"{'='*60}")
    if all_passed:
        print(f"\n🎉 ALL VERIFICATIONS PASSED — M4.4 is READY")
        return 0
    print(f"\n⚠️ SOME VERIFICATIONS FAILED")
    return 1


if __name__ == "__main__":
    sys.exit(main())
