#!/usr/bin/env python3
"""Setup checks for M7.9 — Grounded Local Retrieval."""
from __future__ import annotations

import pathlib
import sys


def main() -> int:
    files = [
        "skos/m7/runtime/markdown_chunking.py",
        "skos/m7/runtime/document_import.py",
        "skos/m4/application/services/embedding_pipeline.py",
        "skos/m4/application/services/semantic_search_service.py",
        "tests/m7/test_markdown_chunking.py",
        "verify_milestone7_9.py",
    ]
    print("M7.9 Setup — Grounded Local Retrieval")
    for file_path in files:
        if not pathlib.Path(file_path).is_file():
            print(f"MISSING {file_path}")
            return 1
        print(f"OK {file_path}")
    version = pathlib.Path("VERSION").read_text(encoding="utf-8").strip()
    if version != "0.7.0-alpha9":
        print(f"FAILED VERSION = {version}")
        return 1
    print(f"OK VERSION = {version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
