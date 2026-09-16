"""Local launch preflight for SKOS operators."""
from __future__ import annotations

from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Any

from skos.m6.production.release import build_release_status


@dataclass(frozen=True)
class LocalLaunchCheck:
    """Single local launch preflight check."""

    name: str
    status: str
    message: str

    @property
    def passed(self) -> bool:
        return self.status == "pass"

    def as_dict(self) -> dict[str, str]:
        return {"name": self.name, "status": self.status, "message": self.message}


@dataclass(frozen=True)
class LocalLaunchPlan:
    """Operator-facing launch plan for local use."""

    ready: bool
    command: str
    admin_url: str
    api_url: str
    checks: tuple[LocalLaunchCheck, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "ready": self.ready,
            "command": self.command,
            "admin_url": self.admin_url,
            "api_url": self.api_url,
            "checks": [check.as_dict() for check in self.checks],
        }


def build_local_launch_plan(
    root_path: str | Path = ".",
    host: str = "127.0.0.1",
    port: int = 8000,
) -> LocalLaunchPlan:
    """Build a non-destructive local launch plan for SKOS."""

    root = Path(root_path)
    checks = (
        _check_release(root),
        _check_config(root),
        _check_admin_assets(),
        _check_local_server_import(),
    )
    base_url = f"http://{host}:{port}"
    return LocalLaunchPlan(
        ready=all(check.passed for check in checks),
        command=(
            "python3 -m uvicorn skos.m6.production.local_server:app "
            f"--host {host} --port {port}"
        ),
        admin_url=f"{base_url}/admin",
        api_url=f"{base_url}/api/v1/health",
        checks=checks,
    )


def _check_release(root: Path) -> LocalLaunchCheck:
    release = build_release_status(root)
    if release.version == "unknown" or release.milestone == "unknown":
        return LocalLaunchCheck("release", "fail", "release metadata is unavailable")
    return LocalLaunchCheck("release", "pass", f"{release.version} ({release.milestone})")


def _check_config(root: Path) -> LocalLaunchCheck:
    config_path = root / "config.yaml"
    if not config_path.is_file():
        return LocalLaunchCheck("config", "fail", "config.yaml is missing")
    text = config_path.read_text(encoding="utf-8")
    required = ("database_path:", "archive_root:", "backup_dir:", "release_dir:")
    missing = [key for key in required if key not in text]
    if missing:
        return LocalLaunchCheck("config", "fail", "missing keys: " + ", ".join(missing))
    return LocalLaunchCheck("config", "pass", "local config keys are present")


def _check_admin_assets() -> LocalLaunchCheck:
    try:
        assets = resources.files("skos.m5.admin_console.assets")
        for filename in ("index.html", "styles.css", "app.js"):
            if not assets.joinpath(filename).is_file():
                return LocalLaunchCheck("admin_assets", "fail", f"missing asset: {filename}")
    except Exception as exc:
        return LocalLaunchCheck("admin_assets", "fail", f"admin assets unavailable: {exc}")
    return LocalLaunchCheck("admin_assets", "pass", "admin console assets are available")


def _check_local_server_import() -> LocalLaunchCheck:
    try:
        from skos.m6.production.local_server import app
    except Exception as exc:
        return LocalLaunchCheck("local_server", "fail", f"local server unavailable: {exc}")
    if app is None:
        return LocalLaunchCheck("local_server", "fail", "local server app is unavailable")
    return LocalLaunchCheck("local_server", "pass", "local server app is importable")
