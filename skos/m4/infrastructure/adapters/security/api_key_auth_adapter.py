"""APIKeyAuthAdapter — Infrastructure Adapter for M4.11.

In-memory API key authentication with configurable key-to-role mapping.
"""
from __future__ import annotations

import secrets
from typing import Any

from skos.m4.infrastructure.ports.auth_port import AuthPort, SecurityContext, AuthError


class APIKeyAuthAdapter(AuthPort):
    """In-memory API key authentication adapter.

    Stores API keys and their associated roles/metadata in memory.
    Suitable for single-instance deployments; for clustered setups
    replace with a shared store adapter.
    """

    def __init__(self, keys: dict[str, dict[str, Any]] | None = None) -> None:
        """Initialize with optional key map.

        Args:
            keys: Mapping of api_key -> {"roles": ["role1", ...], "metadata": {...}}.
        """
        self._keys: dict[str, dict[str, Any]] = {}
        if keys:
            for key, info in keys.items():
                self.register_key(key, **info)

    def register_key(
        self,
        key: str,
        roles: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Register a new API key."""
        self._keys[key] = {
            "roles": list(roles or []),
            "metadata": dict(metadata or {}),
        }

    def revoke_key(self, key: str) -> bool:
        """Revoke an API key. Returns True if key existed."""
        return self._keys.pop(key, None) is not None

    def authenticate(self, credentials: str | None) -> SecurityContext:
        if not credentials:
            return SecurityContext(authenticated=False)

        # Support "Bearer <key>" or raw key
        if credentials.lower().startswith("bearer "):
            credentials = credentials[7:].strip()

        info = self._keys.get(credentials)
        if not info:
            return SecurityContext(authenticated=False)

        return SecurityContext(
            authenticated=True,
            principal=info["metadata"].get("name", credentials[:8] + "..."),
            roles=list(info["roles"]),
            api_key_id=credentials[:8],
            metadata=dict(info["metadata"]),
        )

    def health(self) -> bool:
        return True
