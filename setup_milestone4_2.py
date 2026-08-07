#!/usr/bin/env python3
"""Setup script for Milestone 4.2 — AI Provider Abstraction."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str) -> bool:
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
    print("MILESTONE 4.2 — AI PROVIDER ABSTRACTION")
    print("=" * 60)
    project_root = Path(__file__).parent.resolve()
    print(f"Project root: {project_root}")

    if not run_command([sys.executable, "-m", "pip", "install", "-e", f"{project_root}[dev]"], "Installing skos package with dev dependencies"):
        return 1

    print(f"\n{'='*60}")
    print("Verifying imports...")
    print(f"{'='*60}")
    try:
        import skos.m4.di.container
        import skos.m4.domain.value_objects
        import skos.m4.domain.ai_models
        import skos.m4.infrastructure.adapters.config.hierarchical_config_adapter
        import skos.m4.infrastructure.adapters.secrets.env_secret_adapter
        import skos.m4.infrastructure.adapters.event_bus.in_memory_event_bus
        import skos.m4.infrastructure.adapters.ai_providers.openai_adapter
        import skos.m4.infrastructure.adapters.ai_providers.gemini_adapter
        import skos.m4.infrastructure.adapters.ai_providers.kimi_adapter
        import skos.m4.infrastructure.adapters.ai_providers.claude_adapter
        import skos.m4.infrastructure.adapters.ai_providers.ollama_adapter
        import skos.m4.infrastructure.adapters.ai_providers.provider_registry
        import skos.m4.application.services.ai_service
        print("✅ All core imports successful")
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return 1

    if not run_command([sys.executable, "-m", "pytest", "tests/m4/", "-v", "--tb=short"], "Running M4 test suite"):
        return 1

    print("\n" + "=" * 60)
    print("🎉 M4.2 AI PROVIDER ABSTRACTION SETUP COMPLETE")
    print("=" * 60)
    print("\nYou can now run:")
    print("    python verify_milestone4_2.py")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
