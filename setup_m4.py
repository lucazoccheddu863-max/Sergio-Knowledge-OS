#!/usr/bin/env python3
"""Setup script for Milestone 4.1 — Foundation.

This script:
1. Installs the project package in editable mode (with dev dependencies)
2. Verifies the installation
3. Runs the test suite

Usage:
    python setup_m4.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str) -> bool:
    """Run a shell command and report success/failure."""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"{'='*60}")
    print(f"Command: {' '.join(cmd)}")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.stdout:
        print(result.stdout)
    if result.stderr and result.returncode != 0:
        print(f"STDERR: {result.stderr}")

    if result.returncode == 0:
        print(f"✅ {description} — SUCCESS")
        return True
    else:
        print(f"❌ {description} — FAILED (exit code {result.returncode})")
        return False


def main() -> int:
    print("=" * 60)
    print("MILESTONE 4.1 — FOUNDATION SETUP")
    print("=" * 60)

    project_root = Path(__file__).parent.resolve()
    print(f"Project root: {project_root}")

    # Step 1: Install package in editable mode with dev dependencies
    if not run_command(
        [sys.executable, "-m", "pip", "install", "-e", f"{project_root}[dev]"],
        "Installing skos package with dev dependencies",
    ):
        return 1

    # Step 2: Verify imports work
    print(f"\n{'='*60}")
    print("Verifying imports...")
    print(f"{'='*60}")

    try:
        import skos.m4.di.container
        import skos.m4.domain.value_objects
        import skos.m4.infrastructure.adapters.config.hierarchical_config_adapter
        import skos.m4.infrastructure.adapters.secrets.env_secret_adapter
        print("✅ All core imports successful")
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return 1

    # Step 3: Run tests
    if not run_command(
        [sys.executable, "-m", "pytest", "tests/m4/", "-v", "--tb=short"],
        "Running M4 test suite",
    ):
        return 1

    print("\n" + "=" * 60)
    print("🎉 M4.1 FOUNDATION SETUP COMPLETE")
    print("=" * 60)
    print("\nYou can now run:")
    print("  python verify_milestone4_1_step1.py")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
