"""RBACAuthorizationAdapter — Infrastructure Adapter for M4.11.

Role-based access control with in-memory policy store.
"""
from __future__ import annotations

from skos.m4.infrastructure.ports.authorization_port import (
    AuthorizationPort,
    AuthorizationError,
)
from skos.m4.infrastructure.ports.auth_port import SecurityContext


class RBACAuthorizationAdapter(AuthorizationPort):
    """In-memory RBAC authorization adapter.

    Policies are stored as:
        role -> [(action_pattern, resource_pattern), ...]

    Patterns support wildcard "*" at end.
    """

    def __init__(self, policies: dict[str, list[tuple[str, str]]] | None = None) -> None:
        self._policies: dict[str, list[tuple[str, str]]] = {}
        if policies:
            for role, rules in policies.items():
                self._policies[role] = list(rules)

    def grant(self, role: str, action: str, resource: str) -> None:
        """Grant a role permission on an action/resource pair."""
        self._policies.setdefault(role, []).append((action, resource))

    def revoke(self, role: str, action: str, resource: str) -> bool:
        """Revoke a specific permission. Returns True if removed."""
        rules = self._policies.get(role, [])
        try:
            rules.remove((action, resource))
            return True
        except ValueError:
            return False

    def authorize(self, context: SecurityContext, action: str, resource: str) -> bool:
        if not context.authenticated:
            return False

        for role in context.roles:
            for act_pat, res_pat in self._policies.get(role, []):
                if self._match(action, act_pat) and self._match(resource, res_pat):
                    return True
        return False

    @staticmethod
    def _match(value: str, pattern: str) -> bool:
        if pattern == "*":
            return True
        if pattern.endswith("*"):
            return value.startswith(pattern[:-1])
        return value == pattern

    def health(self) -> bool:
        return True
