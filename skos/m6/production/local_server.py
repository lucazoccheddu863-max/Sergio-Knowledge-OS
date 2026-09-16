"""Local SKOS server entrypoint for the executable application runtime."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI

from skos.m7.runtime import build_application_runtime


def create_app(root_path: str | Path = ".") -> FastAPI:
    """Build the real local application without import-time filesystem writes."""

    return build_application_runtime(root_path=root_path).app


build_local_app = create_app
