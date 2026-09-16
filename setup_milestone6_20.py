#!/usr/bin/env python3
"""Setup script for M6.20 — Operator Snapshot Report Export."""
from __future__ import annotations

import pathlib
import sys


def main() -> int:
    print("=" * 60)
    print("M6.20 Setup — Operator Snapshot Report Export")
    print("=" * 60)

    print("\n[1/4] Checking report export files...")
    files = [
        "skos/m6/production/overview.py",
        "skos/m4/infrastructure/adapters/api/fastapi_adapter.py",
        "skos/m5/admin_console/assets/index.html",
        "skos/m5/admin_console/assets/app.js",
        "tests/m6/test_admin_overview.py",
        "tests/m6/test_admin_readiness_api.py",
    ]
    for file_path in files:
        if pathlib.Path(file_path).exists():
            print(f"  OK {file_path}")
        else:
            print(f"  MISSING {file_path}")
            return 1

    print("\n[2/4] Checking report export wiring...")
    overview_text = pathlib.Path("skos/m6/production/overview.py").read_text(encoding="utf-8")
    api_text = pathlib.Path("skos/m4/infrastructure/adapters/api/fastapi_adapter.py").read_text(
        encoding="utf-8"
    )
    html_text = pathlib.Path("skos/m5/admin_console/assets/index.html").read_text(encoding="utf-8")
    if (
        "render_operator_snapshot_report" in overview_text
        and "/api/v1/admin/snapshot/report" in api_text
        and "snapshot-download" in html_text
    ):
        print("  OK snapshot report export wiring available")
    else:
        print("  FAILED snapshot report export wiring missing")
        return 1

    print("\n[3/4] Checking version consistency...")
    version = pathlib.Path("VERSION").read_text(encoding="utf-8").strip()
    if version == "0.6.0-alpha20":
        print(f"  OK VERSION = {version}")
    else:
        print(f"  FAILED VERSION = {version} (expected 0.6.0-alpha20)")
        return 1

    print("\n[4/4] Checking changelog...")
    changelog = pathlib.Path("CHANGELOG.md").read_text(encoding="utf-8")
    if "M6.20" in changelog and "0.6.0-alpha20" in changelog:
        print("  OK CHANGELOG includes M6.20")
    else:
        print("  FAILED CHANGELOG missing M6.20")
        return 1

    print("\n" + "=" * 60)
    print("M6.20 setup complete. Run: python verify_milestone6_20.py")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
