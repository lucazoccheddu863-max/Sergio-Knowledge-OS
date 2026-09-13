"""Production readiness checks for SKOS.

The checker is intentionally side-effect free: it reports configuration and
filesystem risks without creating directories, opening network sockets, or
requiring external services.
"""
from __future__ import annotations

from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Any

from skos.m4.infrastructure.ports.config_port import ConfigurationPort


VALID_ENVIRONMENTS = {"development", "staging", "production"}


@dataclass(frozen=True)
class ReadinessCheck:
    """Single production readiness check result."""

    name: str
    status: str
    message: str

    @property
    def passed(self) -> bool:
        return self.status != "fail"

    def as_dict(self) -> dict[str, str]:
        return {"name": self.name, "status": self.status, "message": self.message}


@dataclass(frozen=True)
class ReadinessReport:
    """Aggregate readiness report."""

    environment: str
    checks: tuple[ReadinessCheck, ...]

    @property
    def ready(self) -> bool:
        return all(check.passed for check in self.checks)

    def as_dict(self) -> dict[str, Any]:
        return {
            "environment": self.environment,
            "ready": self.ready,
            "checks": [check.as_dict() for check in self.checks],
        }


def run_production_readiness(
    config: ConfigurationPort,
    root_path: str | Path = ".",
) -> ReadinessReport:
    """Run side-effect-free readiness checks for the current runtime config."""

    root = Path(root_path)
    environment = _get_str(config, "m6.environment", "development").lower()
    checks = [
        _check_environment(environment),
        _check_persistence_mode(config, environment),
        _check_security(config, environment),
        _check_required_paths(config, root),
        _check_admin_assets(),
    ]
    return ReadinessReport(environment=environment, checks=tuple(checks))


def _check_environment(environment: str) -> ReadinessCheck:
    if environment in VALID_ENVIRONMENTS:
        return ReadinessCheck("environment", "pass", f"environment is {environment}")
    return ReadinessCheck(
        "environment",
        "fail",
        "m6.environment must be one of: development, staging, production",
    )


def _check_persistence_mode(config: ConfigurationPort, environment: str) -> ReadinessCheck:
    mode = _get_str(config, "m5.persistence.mode", "memory").lower()
    if mode not in {"memory", "persistent", "auto"}:
        return ReadinessCheck(
            "persistence_mode",
            "fail",
            "m5.persistence.mode must be one of: memory, persistent, auto",
        )
    if environment == "production" and mode != "persistent":
        return ReadinessCheck(
            "persistence_mode",
            "fail",
            "production requires m5.persistence.mode=persistent",
        )
    if mode == "auto":
        return ReadinessCheck(
            "persistence_mode",
            "warn",
            "auto mode can fall back to memory; use persistent for production freeze",
        )
    return ReadinessCheck("persistence_mode", "pass", f"persistence mode is {mode}")


def _check_security(config: ConfigurationPort, environment: str) -> ReadinessCheck:
    enabled = _get_bool(config, "m4.security.enabled", False)
    auth_required = _get_bool(config, "m4.security.auth_required", False)
    if environment == "production" and not (enabled and auth_required):
        return ReadinessCheck(
            "security",
            "fail",
            "production requires m4.security.enabled=true and m4.security.auth_required=true",
        )
    if not enabled:
        return ReadinessCheck("security", "warn", "security is disabled")
    if not auth_required:
        return ReadinessCheck("security", "warn", "security is enabled but auth is not required")
    return ReadinessCheck("security", "pass", "security and auth requirement are enabled")


def _check_required_paths(config: ConfigurationPort, root: Path) -> ReadinessCheck:
    path_keys = ("database_path", "archive_root", "backup_dir")
    missing = [key for key in path_keys if not _get_str(config, key, "")]
    if missing:
        return ReadinessCheck("required_paths", "fail", f"missing paths: {', '.join(missing)}")

    invalid: list[str] = []
    for key in path_keys:
        configured = Path(_get_str(config, key, ""))
        path = configured if configured.is_absolute() else root / configured
        parent = path if key != "database_path" else path.parent
        if not parent.exists():
            invalid.append(f"{key} parent does not exist")

    if invalid:
        return ReadinessCheck("required_paths", "fail", "; ".join(invalid))
    return ReadinessCheck("required_paths", "pass", "required storage paths are addressable")


def _check_admin_assets() -> ReadinessCheck:
    try:
        assets = resources.files("skos.m5.admin_console.assets")
        for filename in ("index.html", "styles.css", "app.js"):
            if not assets.joinpath(filename).is_file():
                return ReadinessCheck("admin_assets", "fail", f"missing admin asset: {filename}")
    except Exception as exc:
        return ReadinessCheck("admin_assets", "fail", f"admin assets unavailable: {exc}")
    return ReadinessCheck("admin_assets", "pass", "admin console assets are packaged")


def _get_str(config: ConfigurationPort, path: str, default: str) -> str:
    value = config.get(path, default=default)
    return value if isinstance(value, str) else default


def _get_bool(config: ConfigurationPort, path: str, default: bool) -> bool:
    value = config.get(path, default=default)
    return value if isinstance(value, bool) else default
