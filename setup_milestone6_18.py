#!/usr/bin/env python3
"""Setup script for M6.18 — Admin Console UX Polish."""
from __future__ import annotations

import pathlib
import sys


def main() -> int:
    print("=" * 60)
    print("M6.18 Setup — Admin Console UX Polish")
    print("=" * 60)

    print("\n[1/4] Checking admin console assets...")
    files = [
        "skos/m5/admin_console/assets/index.html",
        "skos/m5/admin_console/assets/app.js",
        "skos/m5/admin_console/assets/styles.css",
        "tests/m6/test_admin_readiness_api.py",
    ]
    for file_path in files:
        if pathlib.Path(file_path).exists():
            print(f"  OK {file_path}")
        else:
            print(f"  MISSING {file_path}")
            return 1

    print("\n[2/4] Checking UX helper wiring...")
    js_text = pathlib.Path("skos/m5/admin_console/assets/app.js").read_text(encoding="utf-8")
    css_text = pathlib.Path("skos/m5/admin_console/assets/styles.css").read_text(encoding="utf-8")
    required_js = ["setLaunchRows", "setBootstrapRows", "setManualRows", "escapeHtml"]
    required_css = ["manual-step", "check-list", "overflow-wrap: anywhere"]
    if all(marker in js_text for marker in required_js) and all(
        marker in css_text for marker in required_css
    ):
        print("  OK console readability helpers available")
    else:
        print("  FAILED console readability helpers missing")
        return 1

    print("\n[3/4] Checking version consistency...")
    version = pathlib.Path("VERSION").read_text(encoding="utf-8").strip()
    if version == "0.6.0-alpha18":
        print(f"  OK VERSION = {version}")
    else:
        print(f"  FAILED VERSION = {version} (expected 0.6.0-alpha18)")
        return 1

    print("\n[4/4] Checking changelog...")
    changelog = pathlib.Path("CHANGELOG.md").read_text(encoding="utf-8")
    if "M6.18" in changelog and "0.6.0-alpha18" in changelog:
        print("  OK CHANGELOG includes M6.18")
    else:
        print("  FAILED CHANGELOG missing M6.18")
        return 1

    print("\n" + "=" * 60)
    print("M6.18 setup complete. Run: python verify_milestone6_18.py")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
