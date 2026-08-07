#!/usr/bin/env python3
"""Setup script for Milestone 4.3 — Embeddings Generation Pipeline."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str) -> bool:
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"{'='*60}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr and result.returncode != 0:
        print(f"STDERR: {result.stderr}")
    if result.returncode == 0:
        print(f"✅ {description} — SUCCESS")
        return True
    print(f"❌ {description} — FAILED")
    return False


def main() -> int:
    print("=" * 60)
    print("MILESTONE 4.3 — EMBEDDINGS GENERATION PIPELINE")
    print("=" * 60)
    project_root = Path(__file__).parent.resolve()

    if not run_command([sys.executable, "-m", "pip", "install", "-e", f"{project_root}[dev]"], "Installing package"):
        return 1

    print(f"\n{'='*60}")
    print("Verifying imports...")
    print(f"{'='*60}")
    try:
        import skos.m4.domain.chunking
        import skos.m4.application.services.embedding_pipeline
        print("✅ All imports successful")
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return 1

    if not run_command([sys.executable, "-m", "pytest", "tests/m4/", "-v", "--tb=short"], "Running M4 test suite"):
        return 1

    print("\n" + "=" * 60)
    print("🎉 M4.3 SETUP COMPLETE")
    print("=" * 60)
    print("\nRun: python verify_milestone4_3.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
