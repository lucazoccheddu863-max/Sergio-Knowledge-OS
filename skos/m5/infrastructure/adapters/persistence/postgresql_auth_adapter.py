"""PostgreSQLAuthAdapter — M5.1 Persistence Layer.

Persistent API key authentication backed by PostgreSQL.
"""
from __future__ import annotations

import hashlib
import secrets
from typing import Any

from ._optional_dependencies import load_psycopg2

from skos.m4.infrastructure.ports.auth_port import AuthPort, SecurityContext, AuthError

psycopg2 = load_psycopg2()


class PostgreSQLAuthAdapter(AuthPort):
    """PostgreSQL-backed API key authentication.

    Stores hashed API keys with roles and metadata.
    """

    def __init__(
        self,
        dsn: str = "postgresql://localhost:5432/skos",
        table_name: str = "api_keys",
    ) -> None:
        self._dsn = dsn
        self._table_name = table_name
        self._conn: psycopg2.extensions.connection | None = None
        self._connect()
        self._ensure_table()

    def _connect(self) -> None:
        try:
            self._conn = psycopg2.connect(self._dsn)
            self._conn.autocommit = True
        except Exception:
            self._conn = None

    def _ensure_table(self) -> None:
        if self._conn is None:
            return
        with self._conn.cursor() as cur:
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {self._table_name} (
                    id SERIAL PRIMARY KEY,
                    key_hash VARCHAR(64) UNIQUE NOT NULL,
                    principal VARCHAR(256) NOT NULL,
                    roles TEXT[] DEFAULT '{{}}',
                    metadata JSONB DEFAULT '{{}}',
                    active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
            """)

    def register_key(
        self,
        key: str,
        principal: str,
        roles: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        if self._conn is None:
            raise AuthError("Database unavailable")
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        with self._conn.cursor() as cur:
            cur.execute(f"""
                INSERT INTO {self._table_name} (key_hash, principal, roles, metadata, active)
                VALUES (%s, %s, %s, %s, TRUE)
                ON CONFLICT (key_hash) DO UPDATE SET
                    principal = EXCLUDED.principal,
                    roles = EXCLUDED.roles,
                    metadata = EXCLUDED.metadata,
                    active = TRUE
            """, (
                key_hash,
                principal,
                list(roles or []),
                psycopg2.extras.Json(metadata or {}),
            ))

    def revoke_key(self, key: str) -> bool:
        if self._conn is None:
            return False
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        with self._conn.cursor() as cur:
            cur.execute(
                f"UPDATE {self._table_name} SET active = FALSE WHERE key_hash = %s",
                (key_hash,),
            )
            return cur.rowcount > 0

    def authenticate(self, credentials: str | None) -> SecurityContext:
        if not credentials or self._conn is None:
            return SecurityContext(authenticated=False)

        if credentials.lower().startswith("bearer "):
            credentials = credentials[7:].strip()

        key_hash = hashlib.sha256(credentials.encode()).hexdigest()
        with self._conn.cursor() as cur:
            cur.execute(f"""
                SELECT principal, roles, metadata
                FROM {self._table_name}
                WHERE key_hash = %s AND active = TRUE
            """, (key_hash,))
            row = cur.fetchone()

        if not row:
            return SecurityContext(authenticated=False)

        principal, roles, metadata = row
        return SecurityContext(
            authenticated=True,
            principal=principal,
            roles=list(roles),
            api_key_id=credentials[:8],
            metadata=dict(metadata) if metadata else {},
        )

    def health(self) -> bool:
        try:
            if self._conn:
                with self._conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    return cur.fetchone() is not None
        except Exception:
            pass
        return False
