"""Tests for one-command local Ollama startup."""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from skos.m7.runtime import local_ai_process


def test_running_ollama_is_reused(monkeypatch) -> None:
    monkeypatch.setattr(local_ai_process, "_ollama_ready", lambda: True)

    result = local_ai_process.ensure_ollama_running()

    assert result.ready is True
    assert result.started is False


def test_installed_ollama_is_started_and_verified(tmp_path: Path, monkeypatch) -> None:
    binary = tmp_path / "ollama"
    binary.write_text("binary", encoding="ascii")
    states = iter((False, True))
    calls: list[list[str]] = []
    monkeypatch.setattr(local_ai_process, "_ollama_ready", lambda: next(states))
    monkeypatch.setattr(local_ai_process, "_find_ollama_binary", lambda: binary)
    monkeypatch.setattr(
        local_ai_process.subprocess,
        "Popen",
        lambda command, **kwargs: calls.append(command) or SimpleNamespace(pid=123),
    )

    result = local_ai_process.ensure_ollama_running(timeout_seconds=1)

    assert result.ready is True
    assert result.started is True
    assert calls == [[str(binary), "serve"]]


def test_missing_ollama_returns_actionable_failure(monkeypatch) -> None:
    monkeypatch.setattr(local_ai_process, "_ollama_ready", lambda: False)
    monkeypatch.setattr(local_ai_process, "_find_ollama_binary", lambda: None)

    result = local_ai_process.ensure_ollama_running()

    assert result.ready is False
    assert result.started is False
    assert "not installed" in result.message
