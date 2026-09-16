"""Operator command-line entrypoint for local Sergio Knowledge OS use."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence, TextIO
import sys

from skos.m4.infrastructure.adapters.config.hierarchical_config_adapter import (
    HierarchicalConfigAdapter,
)
from skos.m6.production.launch import bootstrap_local_workspace, build_local_launch_plan
from skos.m6.production.overview import build_operator_snapshot, render_operator_snapshot_report


def build_parser() -> argparse.ArgumentParser:
    """Build the operator CLI parser."""

    parser = argparse.ArgumentParser(prog="sergio-knowledge", description="Operate Sergio Knowledge OS")
    parser.add_argument("--root", default=".", help="Repository root (default: current directory)")
    parser.add_argument("--host", default="127.0.0.1", help="Local server host")
    parser.add_argument("--port", default=8000, type=int, help="Local server port")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("prepare", help="Prepare local folders safely")
    commands.add_parser("status", help="Show the current operator status")
    report = commands.add_parser("report", help="Save an operator snapshot report")
    report.add_argument("--output", type=Path, help="Report destination path")
    report.add_argument("--overwrite", action="store_true", help="Replace an existing report")
    commands.add_parser("start", help="Prepare and start the local admin console")
    return parser


def build_operator_config(root: Path) -> HierarchicalConfigAdapter:
    """Build local operator configuration with paths anchored to the selected root."""

    data_dir = root / "data"
    return HierarchicalConfigAdapter(
        defaults={
            "database_path": str(data_dir / "sergio_knowledge.db"),
            "archive_root": str(data_dir / "archive"),
            "backup_dir": str(data_dir / "backups"),
            "release_dir": str(data_dir / "releases"),
            "m4": {"security": {"enabled": False, "auth_required": False}},
            "m5": {"persistence": {"mode": "memory"}},
            "m6": {"environment": "development"},
        }
    )


def run_command(
    args: argparse.Namespace,
    stdout: TextIO = sys.stdout,
    stderr: TextIO = sys.stderr,
) -> int:
    """Execute one parsed operator command."""

    root = Path(args.root).resolve()
    config = build_operator_config(root)

    if args.command == "prepare":
        result = _prepare(root, config)
        print("Workspace ready" if result.ready else "Workspace needs attention", file=stdout)
        for item in result.items:
            state = "created" if item.created else "present"
            print(f"- {item.name}: {state} ({item.path})", file=stdout)
        for warning in result.warnings:
            print(f"Warning: {warning}", file=stderr)
        return 0 if result.ready else 1

    if args.command in {"status", "report"}:
        snapshot = build_operator_snapshot(config, root_path=root, host=args.host, port=args.port)
        report = render_operator_snapshot_report(snapshot)
        if args.command == "status":
            print(report, end="", file=stdout)
            return 0 if snapshot.ready else 1

        output = args.output or root / "data" / "reports" / _report_filename(snapshot.release.version)
        try:
            _write_report(output, report, overwrite=args.overwrite)
        except FileExistsError:
            print(f"Report already exists: {output}", file=stderr)
            print("Use --overwrite to replace it.", file=stderr)
            return 2
        print(f"Report saved: {output}", file=stdout)
        return 0

    result = _prepare(root, config)
    plan = build_local_launch_plan(root_path=root, host=args.host, port=args.port)
    if not result.ready or not plan.ready:
        print("Local start blocked by failed preflight checks.", file=stderr)
        for warning in result.warnings:
            print(f"- {warning}", file=stderr)
        for check in plan.checks:
            if not check.passed:
                print(f"- {check.name}: {check.message}", file=stderr)
        return 1
    print(f"Admin console: {plan.admin_url}", file=stdout)
    print("Press Ctrl+C to stop Sergio Knowledge OS.", file=stdout)
    _run_server(args.host, args.port)
    return 0


def _prepare(root: Path, config: HierarchicalConfigAdapter):
    return bootstrap_local_workspace(
        root_path=root,
        database_path=config.get("database_path"),
        archive_root=config.get("archive_root"),
        backup_dir=config.get("backup_dir"),
        release_dir=config.get("release_dir"),
    )


def _report_filename(version: str) -> str:
    return f"sergio-operator-snapshot-{version}.txt"


def _write_report(path: Path, content: str, overwrite: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = "w" if overwrite else "x"
    with path.open(mode, encoding="utf-8") as report_file:
        report_file.write(content)


def _run_server(host: str, port: int) -> None:
    import uvicorn

    uvicorn.run("skos.m6.production.local_server:app", host=host, port=port)


def main(argv: Sequence[str] | None = None) -> int:
    """Parse arguments and run the operator command."""

    return run_command(build_parser().parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
