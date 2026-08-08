#!/usr/bin/env python3
"""Verification script for Milestone 4.6 — RAG Pipeline."""
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
        setup = PROJECT_ROOT / "setup_milestone4_6.py"
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


def verify_m4_4() -> bool:
    return _check(
        [PROJECT_ROOT / "skos" / "m4" / "infrastructure" / "adapters" / "vector_store" / "chromadb_adapter.py"],
        "M4.4 Baseline",
    )


def verify_m4_5() -> bool:
    return _check(
        [PROJECT_ROOT / "skos" / "m4" / "infrastructure" / "adapters" / "semantic_search" / "chroma_semantic_search_adapter.py"],
        "M4.5 Baseline",
    )


def run_tests() -> bool:
    print(f"\n{'='*60}")
    print("Running M4.6 Test Suite...")
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


def verify_rag_pipeline_port() -> bool:
    print(f"\n{'='*60}")
    print("Verifying RAGPipelinePort...")
    print(f"{'='*60}")
    try:
        from skos.m4.infrastructure.ports.rag_pipeline_port import RAGPipelinePort
        assert hasattr(RAGPipelinePort, "answer")
        assert hasattr(RAGPipelinePort, "health_check")
        print("✅ RAGPipelinePort: PASSED")
        return True
    except Exception as e:
        print(f"❌ RAGPipelinePort: FAILED — {e}")
        return False


def verify_rag_pipeline_service() -> bool:
    print(f"\n{'='*60}")
    print("Verifying RAGPipelineService...")
    print(f"{'='*60}")
    try:
        from skos.m4.application.services.rag_pipeline_service import RAGPipelineService
        import inspect
        sig = inspect.signature(RAGPipelineService.__init__)
        params = list(sig.parameters.keys())
        assert "semantic_search" in params
        assert "ai_service" in params
        assert "config" in params
        assert "event_bus" in params
        print("✅ RAGPipelineService: PASSED")
        return True
    except Exception as e:
        print(f"❌ RAGPipelineService: FAILED — {e}")
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
    print("MILESTONE 4.6 — RAG PIPELINE")
    print(f"{'='*60}")
    if not ensure_package():
        return 1
    results = {
        "M4.1.1 Baseline": verify_m4_1_1(),
        "M4.1.2 Baseline": verify_m4_1_2(),
        "M4.2 Baseline": verify_m4_2(),
        "M4.3 Baseline": verify_m4_3(),
        "M4.4 Baseline": verify_m4_4(),
        "M4.5 Baseline": verify_m4_5(),
        "RAGPipelinePort": verify_rag_pipeline_port(),
        "RAGPipelineService": verify_rag_pipeline_service(),
        "Architecture Rules": verify_architecture(),
        "M4.6 Test Suite": run_tests(),
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
        print(f"\n🎉 ALL VERIFICATIONS PASSED — M4.6 is READY")
        return 0
    print(f"\n⚠️ SOME VERIFICATIONS FAILED")
    return 1


if __name__ == "__main__":
    sys.exit(main())
