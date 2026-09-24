"""Tests for the M6 operator command-line entrypoint."""
from __future__ import annotations

from io import StringIO
from pathlib import Path
from types import SimpleNamespace

from skos.m6.production import operator_cli
import skos.m7.runtime


def parse(*args: str):
    return operator_cli.build_parser().parse_args(args)


def seed_release_files(root: Path) -> None:
    (root / "VERSION").write_text("0.6.0-alpha21\n", encoding="utf-8")
    (root / "config.yaml").write_text(
        "database_path: data/sergio_knowledge.db\n"
        "archive_root: data/archive\n"
        "backup_dir: data/backups\n"
        "release_dir: data/releases\n",
        encoding="utf-8",
    )


def test_prepare_command_creates_local_workspace(tmp_path: Path) -> None:
    output = StringIO()

    result = operator_cli.run_command(parse("--root", str(tmp_path), "prepare"), stdout=output)

    assert result == 0
    assert "Workspace ready" in output.getvalue()
    assert (tmp_path / "data" / "archive").is_dir()
    assert (tmp_path / "data" / "backups").is_dir()


def test_status_command_prints_operator_snapshot(tmp_path: Path) -> None:
    seed_release_files(tmp_path)
    operator_cli.run_command(parse("--root", str(tmp_path), "prepare"), stdout=StringIO())
    output = StringIO()

    result = operator_cli.run_command(parse("--root", str(tmp_path), "status"), stdout=output)

    assert result == 0
    assert "Sergio Knowledge OS - Operator Snapshot" in output.getvalue()
    assert "Verdict: READY" in output.getvalue()


def test_report_command_protects_existing_report(tmp_path: Path) -> None:
    seed_release_files(tmp_path)
    output_path = tmp_path / "snapshot.txt"
    output_path.write_text("keep me", encoding="utf-8")
    errors = StringIO()

    result = operator_cli.run_command(
        parse("--root", str(tmp_path), "report", "--output", str(output_path)),
        stdout=StringIO(),
        stderr=errors,
    )

    assert result == 2
    assert output_path.read_text(encoding="utf-8") == "keep me"
    assert "Use --overwrite" in errors.getvalue()

    overwrite_result = operator_cli.run_command(
        parse(
            "--root",
            str(tmp_path),
            "report",
            "--output",
            str(output_path),
            "--overwrite",
        ),
        stdout=StringIO(),
    )
    assert overwrite_result == 0
    assert "Sergio Knowledge OS - Operator Snapshot" in output_path.read_text(encoding="utf-8")


def test_start_command_runs_server_after_preflight(tmp_path: Path, monkeypatch) -> None:
    seed_release_files(tmp_path)
    calls: list[tuple[str, int]] = []
    monkeypatch.setattr(operator_cli, "_run_server", lambda host, port: calls.append((host, port)))
    monkeypatch.setattr(
        operator_cli,
        "_ensure_local_ai",
        lambda: SimpleNamespace(ready=True, started=True, message="Ollama started"),
    )
    output = StringIO()

    result = operator_cli.run_command(
        parse("--root", str(tmp_path), "--port", "8765", "start"),
        stdout=output,
    )

    assert result == 0
    assert calls == [("127.0.0.1", 8765)]
    assert "Ollama started" in output.getvalue()
    assert "http://127.0.0.1:8765/admin" in output.getvalue()


def test_start_command_stops_when_local_ai_is_unavailable(tmp_path: Path, monkeypatch) -> None:
    seed_release_files(tmp_path)
    calls: list[tuple[str, int]] = []
    monkeypatch.setattr(operator_cli, "_run_server", lambda host, port: calls.append((host, port)))
    monkeypatch.setattr(
        operator_cli,
        "_ensure_local_ai",
        lambda: SimpleNamespace(ready=False, started=False, message="Ollama unavailable"),
    )
    errors = StringIO()

    result = operator_cli.run_command(
        parse("--root", str(tmp_path), "start"),
        stdout=StringIO(),
        stderr=errors,
    )

    assert result == 1
    assert calls == []
    assert "Ollama unavailable" in errors.getvalue()


def test_import_command_reports_archived_document(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "notes.txt"
    source.write_text("local knowledge", encoding="utf-8")
    result = SimpleNamespace(
        status="imported",
        source_path=str(source),
        archived_path=str(tmp_path / "archive" / "notes.txt"),
        sha256="a" * 64,
        chunk_count=1,
    )
    importer = SimpleNamespace(import_file=lambda path: result)
    runtime = SimpleNamespace(document_import=importer)
    monkeypatch.setattr(skos.m7.runtime, "build_application_runtime", lambda root: runtime)
    output = StringIO()

    exit_code = operator_cli.run_command(
        parse("--root", str(tmp_path), "import", str(source)),
        stdout=output,
    )

    assert exit_code == 0
    assert "Document imported" in output.getvalue()
    assert "Indexed chunks: 1" in output.getvalue()
