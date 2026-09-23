"""Start and verify the local Ollama process for one-command operation."""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import shutil
import subprocess
import time
import urllib.request


OLLAMA_VERSION_URL = "http://127.0.0.1:11434/api/version"


@dataclass(frozen=True)
class LocalAIStartResult:
    ready: bool
    started: bool
    message: str


def ensure_ollama_running(timeout_seconds: float = 20.0) -> LocalAIStartResult:
    """Return a ready Ollama instance, starting the local binary when needed."""

    if _ollama_ready():
        return LocalAIStartResult(True, False, "Ollama is already running")

    binary = _find_ollama_binary()
    if binary is None:
        return LocalAIStartResult(False, False, "Ollama is not installed or is not on PATH")

    environment = os.environ.copy()
    environment.setdefault("OLLAMA_FLASH_ATTENTION", "1")
    environment.setdefault("OLLAMA_KV_CACHE_TYPE", "q8_0")
    try:
        subprocess.Popen(
            [str(binary), "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=environment,
            start_new_session=True,
        )
    except OSError as exc:
        return LocalAIStartResult(False, False, f"Ollama could not start: {exc}")

    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if _ollama_ready():
            return LocalAIStartResult(True, True, f"Ollama started from {binary}")
        time.sleep(0.25)
    return LocalAIStartResult(False, True, "Ollama did not become ready in time")


def _ollama_ready() -> bool:
    try:
        with urllib.request.urlopen(OLLAMA_VERSION_URL, timeout=2) as response:
            return response.status == 200
    except Exception:
        return False


def _find_ollama_binary() -> Path | None:
    candidates = [
        shutil.which("ollama"),
        "/usr/local/opt/ollama/bin/ollama",
        "/opt/homebrew/bin/ollama",
    ]
    for candidate in candidates:
        if candidate:
            path = Path(candidate)
            if path.is_file() and os.access(path, os.X_OK):
                return path
    return None
