"""Environment variable secret manager adapter."""
from __future__ import annotations

import os

from skos.m4.domain.value_objects import SecretRef
from skos.m4.infrastructure.ports.secret_port import SecretAccessError, SecretManagerPort, SecretNotFoundError


class EnvSecretManagerAdapter(SecretManagerPort):
    ENV_PREFIX = "SKOS_SECRET__"

    def _env_key(self, ref: SecretRef) -> str:
        if ref.namespace == "default":
            return f"{self.ENV_PREFIX}{ref.key.upper()}"
        return f"{self.ENV_PREFIX}{ref.namespace.upper()}__{ref.key.upper()}"

    def get(self, ref: SecretRef) -> str:
        env_key = self._env_key(ref)
        value = os.environ.get(env_key)
        if value is None:
            raise SecretNotFoundError(f"Secret not found: {ref.key} (namespace: {ref.namespace})")
        return value

    def set(self, ref: SecretRef, value: str) -> None:
        env_key = self._env_key(ref)
        os.environ[env_key] = value

    def delete(self, ref: SecretRef) -> None:
        env_key = self._env_key(ref)
        if env_key not in os.environ:
            raise SecretNotFoundError(f"Secret not found: {ref.key} (namespace: {ref.namespace})")
        del os.environ[env_key]

    def exists(self, ref: SecretRef) -> bool:
        return self._env_key(ref) in os.environ

    def list_keys(self, namespace: str = "default") -> list[str]:
        prefix = f"{self.ENV_PREFIX}{namespace.upper()}__" if namespace != "default" else self.ENV_PREFIX
        keys = []
        for key in os.environ:
            if key.startswith(prefix):
                secret_key = key[len(prefix):].lower()
                keys.append(secret_key)
        return sorted(keys)
