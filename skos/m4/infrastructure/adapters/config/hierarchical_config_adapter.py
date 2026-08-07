"""Hierarchical configuration adapter."""
from __future__ import annotations

import json
import os
import re
from copy import deepcopy
from pathlib import Path
from typing import Any, Callable

from skos.m4.domain.value_objects import ConfigPath, ConfigScope
from skos.m4.infrastructure.ports.config_port import ConfigSubscription, ConfigurationPort


class HierarchicalConfigAdapter(ConfigurationPort):
    ENV_PREFIX = "SKOS_M4_"

    def __init__(self, defaults: dict[str, Any] | None = None, env_prefix: str = "SKOS_M4_") -> None:
        self._env_prefix = env_prefix
        self._scopes: dict[tuple, dict[str, Any]] = {}
        self._subscribers: dict[str, list[ConfigSubscription]] = {}
        system_scope = ConfigScope()
        self._scopes[system_scope.to_tuple()] = deepcopy(defaults) if defaults else {}
        self._load_env_vars(system_scope)

    def _load_env_vars(self, scope: ConfigScope) -> None:
        pattern = re.compile(re.escape(self._env_prefix) + r"(.+)")
        for key, value in os.environ.items():
            match = pattern.match(key)
            if match:
                path = match.group(1).lower().replace("__", ".")
                typed_value = self._coerce_type(value)
                self._set_in_scope(scope, path, typed_value, notify=False)

    @staticmethod
    def _coerce_type(value: str) -> Any:
        lower = value.lower()
        if lower in ("true", "1", "yes", "on"):
            return True
        if lower in ("false", "0", "no", "off"):
            return False
        if lower in ("null", "none", "nil"):
            return None
        try:
            return int(value)
        except ValueError:
            pass
        try:
            return float(value)
        except ValueError:
            pass
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            pass
        return value

    def _get_scope_data(self, scope: ConfigScope) -> dict[str, Any]:
        key = scope.to_tuple()
        if key not in self._scopes:
            self._scopes[key] = {}
        return self._scopes[key]

    def _set_in_scope(self, scope: ConfigScope, path: str, value: Any, notify: bool = True) -> None:
        data = self._get_scope_data(scope)
        parts = path.split(".")
        for part in parts[:-1]:
            if part not in data or not isinstance(data[part], dict):
                data[part] = {}
            data = data[part]
        old_value = data.get(parts[-1])
        data[parts[-1]] = value
        if notify and old_value != value:
            self._notify(path, value)

    def _get_from_scope(self, scope: ConfigScope, path: str) -> Any:
        data = self._get_scope_data(scope)
        parts = path.split(".")
        for part in parts:
            if not isinstance(data, dict) or part not in data:
                raise KeyError(path)
            data = data[part]
        return data

    def _notify(self, path: str, value: Any) -> None:
        for sub in self._subscribers.get(path, []):
            if sub.active:
                try:
                    sub.callback(value)
                except Exception:
                    pass

    def get(self, path: str | ConfigPath, scope: ConfigScope | None = None, default: Any = None) -> Any:
        if isinstance(path, ConfigPath):
            path = str(path)
        target_scope = scope or ConfigScope()
        scopes_to_try = [target_scope]
        if target_scope.user_id:
            scopes_to_try.append(ConfigScope(tenant_id=target_scope.tenant_id, workspace_id=target_scope.workspace_id, project_id=target_scope.project_id))
        if target_scope.project_id:
            scopes_to_try.append(ConfigScope(tenant_id=target_scope.tenant_id, workspace_id=target_scope.workspace_id))
        if target_scope.workspace_id:
            scopes_to_try.append(ConfigScope(tenant_id=target_scope.tenant_id))
        if target_scope.tenant_id:
            scopes_to_try.append(ConfigScope())
        for s in scopes_to_try:
            try:
                return self._get_from_scope(s, path)
            except KeyError:
                continue
        return default

    def get_with_fallback(self, path: str | ConfigPath, scopes: list[ConfigScope], default: Any = None) -> Any:
        if isinstance(path, ConfigPath):
            path = str(path)
        for scope in scopes:
            try:
                return self._get_from_scope(scope, path)
            except KeyError:
                continue
        return default

    def set(self, path: str | ConfigPath, value: Any, scope: ConfigScope | None = None) -> None:
        if isinstance(path, ConfigPath):
            path = str(path)
        target_scope = scope or ConfigScope()
        self._set_in_scope(target_scope, path, value)

    def subscribe(self, path: str | ConfigPath, callback: Callable[[Any], None]) -> ConfigSubscription:
        if isinstance(path, ConfigPath):
            path = str(path)
        sub = ConfigSubscription(path, callback)
        self._subscribers.setdefault(path, []).append(sub)
        return sub

    def reload(self, scope: ConfigScope | None = None) -> None:
        target = scope or ConfigScope()
        self._load_env_vars(target)

    def dump(self, scope: ConfigScope | None = None) -> dict[str, Any]:
        target = scope or ConfigScope()
        result = deepcopy(self._get_scope_data(ConfigScope()))
        if target.tenant_id:
            tenant_data = self._get_scope_data(ConfigScope(tenant_id=target.tenant_id))
            self._deep_merge(result, tenant_data)
        if target.workspace_id:
            ws_data = self._get_scope_data(ConfigScope(tenant_id=target.tenant_id, workspace_id=target.workspace_id))
            self._deep_merge(result, ws_data)
        if target.project_id:
            proj_data = self._get_scope_data(ConfigScope(tenant_id=target.tenant_id, workspace_id=target.workspace_id, project_id=target.project_id))
            self._deep_merge(result, proj_data)
        if target.user_id:
            user_data = self._get_scope_data(target)
            self._deep_merge(result, user_data)
        return result

    @staticmethod
    def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> None:
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                HierarchicalConfigAdapter._deep_merge(base[key], value)
            else:
                base[key] = deepcopy(value)

    def load_from_file(self, file_path: str | Path, scope: ConfigScope | None = None) -> None:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")
        with open(path, "r", encoding="utf-8") as f:
            if path.suffix in (".yaml", ".yml"):
                try:
                    import yaml
                    data = yaml.safe_load(f)
                except ImportError:
                    raise ImportError("PyYAML is required for YAML config files")
            else:
                data = json.load(f)
        target_scope = scope or ConfigScope()
        for key, value in (data or {}).items():
            self._set_in_scope(target_scope, key, value, notify=False)
