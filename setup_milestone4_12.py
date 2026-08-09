#!/usr/bin/env python3
"""Setup script for M4.12 — Release Engineering / Production Readiness."""
from __future__ import annotations
import pathlib
import sys

def main() -> int:
    print("=" * 60)
    print("M4.12 Setup — Release Engineering / Production Readiness")
    print("=" * 60)

    print("\n[1/8] Checking production documentation...")
    docs = [
        "README.md",
        "docs/ARCHITECTURE.md",
        "docs/ROADMAP.md",
        "docs/api_contract.md",
        "docs/ADR.md",
        "docs/SECURITY_CHECKLIST.md",
        "docs/BENCHMARK_REPORT.md",
    ]
    for d in docs:
        if pathlib.Path(d).exists():
            print(f"  ✅ {d}")
        else:
            print(f"  ❌ {d} MISSING")
            return 1

    print("\n[2/8] Checking SBOM...")
    if pathlib.Path("SBOM.json").exists():
        print("  ✅ SBOM.json")
    else:
        print("  ❌ SBOM.json MISSING")
        return 1

    print("\n[3/8] Checking VERSION...")
    with open("VERSION") as f:
        version = f.read().strip()
    if version == "0.4.0":
        print(f"  ✅ VERSION = {version}")
    else:
        print(f"  ❌ VERSION = {version} (expected 0.4.0)")
        return 1

    print("\n[4/8] Checking CHANGELOG...")
    with open("CHANGELOG.md") as f:
        content = f.read()
    if "0.4.0" in content and "M4.12" in content:
        print("  ✅ CHANGELOG includes M4.12")
    else:
        print("  ❌ CHANGELOG missing M4.12")
        return 1

    print("\n[5/8] Checking all milestone artifacts...")
    for i in range(1, 13):
        if i == 1:
            for step in ["1", "2"]:
                setup = f"setup_milestone4_1_step{step}.py"
                verify = f"verify_milestone4_1_step{step}.py"
                if pathlib.Path(setup).exists() and pathlib.Path(verify).exists():
                    print(f"  ✅ M4.1 Step {step}")
                else:
                    print(f"  ❌ M4.1 Step {step} MISSING")
                    return 1
        elif i in [4, 9]:
            setup = f"setup_milestone4_{i}.py"
            verify = f"verify_milestone4_{i}.py"
            if pathlib.Path(setup).exists() and pathlib.Path(verify).exists():
                print(f"  ✅ M4.{i}")
            else:
                print(f"  ❌ M4.{i} MISSING")
                return 1
        elif i == 10:
            setup = "setup_milestone4_10.py"
            verify = "verify_milestone4_10.py"
            if pathlib.Path(setup).exists() and pathlib.Path(verify).exists():
                print(f"  ✅ M4.{i}")
            else:
                print(f"  ❌ M4.{i} MISSING")
                return 1
        elif i == 11:
            setup = "setup_milestone4_11.py"
            verify = "verify_milestone4_11.py"
            if pathlib.Path(setup).exists() and pathlib.Path(verify).exists():
                print(f"  ✅ M4.{i}")
            else:
                print(f"  ❌ M4.{i} MISSING")
                return 1
        elif i == 12:
            setup = "setup_milestone4_12.py"
            verify = "verify_milestone4_12.py"
            if pathlib.Path(setup).exists() and pathlib.Path(verify).exists():
                print(f"  ✅ M4.{i}")
            else:
                print(f"  ❌ M4.{i} MISSING")
                return 1
        else:
            setup = f"setup_milestone4_{i}.py"
            verify = f"verify_milestone4_{i}.py"
            if pathlib.Path(setup).exists() and pathlib.Path(verify).exists():
                print(f"  ✅ M4.{i}")
            else:
                print(f"  ❌ M4.{i} MISSING")
                return 1

    print("\n[6/8] Checking M2/M3 artifacts...")
    for artifact in ["setup_milestone2.py", "verify_milestone2.py",
                     "setup_milestone3.py", "verify_milestone3.py"]:
        if pathlib.Path(artifact).exists():
            print(f"  ✅ {artifact}")
        else:
            print(f"  ❌ {artifact} MISSING")
            return 1

    print("\n[7/8] Checking pyproject.toml...")
    with open("pyproject.toml") as f:
        content = f.read()
    if 'version = "0.4.0"' in content or 'version = "0.4.0-alpha' in content:
        print("  ✅ pyproject.toml version present")
    else:
        print("  ❌ pyproject.toml version missing")
        return 1

    print("\n[8/8] Checking test suite...")
    test_files = list(pathlib.Path("tests/m4").glob("test_*.py"))
    print(f"  ✅ {len(test_files)} test files found")

    print("\n" + "=" * 60)
    print("M4.12 setup complete. Run: python verify_milestone4_12.py")
    print("=" * 60)
    return 0

if __name__ == "__main__":
    sys.exit(main())
