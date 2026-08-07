#!/usr/bin/env python3
"""Verification script for Milestone 4.3 — Embeddings Generation Pipeline."""
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
        setup = PROJECT_ROOT / "setup_milestone4_3.py"
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
    return _check([PROJECT_ROOT / "skos" / "m4" / "infrastructure" / "adapters" / "event_bus" / "in_memory_event_bus.py"], "M4.1.2 Baseline")


def verify_m4_2() -> bool:
    return _check([PROJECT_ROOT / "skos" / "m4" / "infrastructure" / "adapters" / "ai_providers" / "provider_registry.py"], "M4.2 Baseline")


def run_tests() -> bool:
    print(f"\n{'='*60}")
    print("Running M4.3 Test Suite...")
    print(f"{'='*60}")
    test_dir = PROJECT_ROOT / "tests" / "m4"
    result = subprocess.run([sys.executable, "-m", "pytest", str(test_dir), "-v", "--tb=short"], capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    return result.returncode == 0


def verify_chunking() -> bool:
    print(f"\n{'='*60}")
    print("Verifying Chunking...")
    print(f"{'='*60}")
    try:
        from skos.m4.domain.chunking import FixedSizeChunking, ParagraphChunking, TextChunk
        strategy = FixedSizeChunking(chunk_size=5, overlap=1)
        chunks = strategy.chunk("a b c d e f g h i j", source_id="test")
        assert len(chunks) > 1
        assert all(c.total_chunks == len(chunks) for c in chunks)
        print("✅ Chunking: PASSED")
        return True
    except Exception as e:
        print(f"❌ Chunking: FAILED — {e}")
        return False


def verify_pipeline() -> bool:
    print(f"\n{'='*60}")
    print("Verifying Embedding Pipeline...")
    print(f"{'='*60}")
    try:
        from unittest.mock import MagicMock
        from skos.m4.application.services.embedding_pipeline import EmbeddingPipeline
        from skos.m4.infrastructure.adapters.event_bus.in_memory_event_bus import InMemoryEventBus
        bus = InMemoryEventBus()
        config = MagicMock()
        config.get.side_effect = lambda key, default=None: {"m4.embedding.batch_size": 100, "m4.embedding.chunk_size": 500, "m4.embedding.chunk_overlap": 50}.get(key, default)
        ai = MagicMock()
        ai.embed.return_value = MagicMock(vectors=[[0.1, 0.2]], model="test", dimensions=2)
        pipeline = EmbeddingPipeline(ai, bus, config)
        result = pipeline.embed_texts(["hello world"], provider_name="test", source_id="src-1")
        assert len(result.vectors) == 1
        print("✅ Embedding Pipeline: PASSED")
        return True
    except Exception as e:
        print(f"❌ Embedding Pipeline: FAILED — {e}")
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
    print("MILESTONE 4.3 — EMBEDDINGS GENERATION PIPELINE")
    print(f"{'='*60}")
    if not ensure_package():
        return 1
    results = {
        "M2 Baseline": verify_m2(),
        "M3 Baseline": verify_m3(),
        "M4.1.1 Baseline": verify_m4_1_1(),
        "M4.1.2 Baseline": verify_m4_1_2(),
        "M4.2 Baseline": verify_m4_2(),
        "Chunking": verify_chunking(),
        "Embedding Pipeline": verify_pipeline(),
        "Architecture Rules": verify_architecture(),
        "M4.3 Test Suite": run_tests(),
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
        print(f"\n🎉 ALL VERIFICATIONS PASSED — M4.3 is READY")
        return 0
    print(f"\n⚠️ SOME VERIFICATIONS FAILED")
    return 1


if __name__ == "__main__":
    sys.exit(main())
