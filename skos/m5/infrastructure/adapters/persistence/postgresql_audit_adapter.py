"""PostgreSQLAuditAdapter — M5.1 Persistence Layer.

Persistent audit logging to PostgreSQL.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from ._optional_dependencies import load_psycopg2

from skos.m4.infrastructure.ports.audit_port import AuditPort, AuditEvent

psycopg2 = load_psycopg2()


class PostgreSQLAuditAdapter(AuditPort):
    """PostgreSQL-backed structured audit logger.

    Stores audit events in a dedicated table with JSONB for flexible details.
    """

    def __init__(
        self,
        dsn: str = "postgresql://localhost:5432/skos",
        table_name: str = "audit_events",
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
                    timestamp TIMESTAMPTZ NOT NULL,
                    event_type VARCHAR(64) NOT NULL,
                    principal VARCHAR(256),
                    action VARCHAR(64) NOT NULL,
                    resource VARCHAR(512) NOT NULL,
                    status VARCHAR(32) NOT NULL,
                    details JSONB DEFAULT '{{}}',
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
                CREATE INDEX IF NOT EXISTS idx_audit_timestamp 
                    ON {self._table_name}(timestamp DESC);
                CREATE INDEX IF NOT EXISTS idx_audit_principal 
                    ON {self._table_name}(principal);
                CREATE INDEX IF NOT EXISTS idx_audit_event_type 
                    ON {self._table_name}(event_type);
            """)

    def record(self, event: AuditEvent) -> None:
        if self._conn is None:
            return
        with self._conn.cursor() as cur:
            cur.execute(f"""
                INSERT INTO {self._table_name} 
                (timestamp, event_type, principal, action, resource, status, details)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                event.timestamp,
                event.event_type,
                event.principal,
                event.action,
                event.resource,
                event.status,
                json.dumps(event.details),
            ))

    def health(self) -> bool:
        try:
            if self._conn:
                with self._conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    return cur.fetchone() is not None
        except Exception:
            pass
        return False
