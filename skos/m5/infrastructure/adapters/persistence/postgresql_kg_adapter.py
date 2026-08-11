"""PostgreSQLKnowledgeGraphAdapter — M5.1 Persistence Layer.

Persistent knowledge graph backed by PostgreSQL.
Uses adjacency list model: entities table + relations table.
"""
from __future__ import annotations

import json
from typing import Any

from ._optional_dependencies import load_psycopg2

from skos.m4.infrastructure.ports.knowledge_graph_port import (
    KnowledgeGraphPort, KnowledgeGraphError,
)
from skos.m4.domain.knowledge_graph_models import Entity, GraphQuery, GraphResult, Relation

psycopg2 = load_psycopg2()


class PostgreSQLKnowledgeGraphAdapter(KnowledgeGraphPort):
    """PostgreSQL-backed knowledge graph.

    Entities and relations stored in normalized tables.
    Graph traversal via recursive CTEs.
    """

    def __init__(
        self,
        dsn: str = "postgresql://localhost:5432/skos",
    ) -> None:
        self._dsn = dsn
        self._conn: psycopg2.extensions.connection | None = None
        self._connect()
        self._ensure_tables()

    def _connect(self) -> None:
        try:
            self._conn = psycopg2.connect(self._dsn)
            self._conn.autocommit = True
        except Exception:
            self._conn = None

    def _ensure_tables(self) -> None:
        if self._conn is None:
            return
        with self._conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS kg_entities (
                    id VARCHAR(256) PRIMARY KEY,
                    name VARCHAR(512) NOT NULL,
                    entity_type VARCHAR(128) NOT NULL,
                    metadata JSONB DEFAULT '{}',
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                );
                CREATE INDEX IF NOT EXISTS idx_kg_entities_name 
                    ON kg_entities USING gin(to_tsvector('simple', name));
                CREATE INDEX IF NOT EXISTS idx_kg_entities_type 
                    ON kg_entities(entity_type);

                CREATE TABLE IF NOT EXISTS kg_relations (
                    id SERIAL PRIMARY KEY,
                    source_id VARCHAR(256) NOT NULL REFERENCES kg_entities(id) ON DELETE CASCADE,
                    target_id VARCHAR(256) NOT NULL REFERENCES kg_entities(id) ON DELETE CASCADE,
                    relation_type VARCHAR(128) NOT NULL,
                    metadata JSONB DEFAULT '{}',
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    UNIQUE(source_id, target_id, relation_type)
                );
                CREATE INDEX IF NOT EXISTS idx_kg_relations_source 
                    ON kg_relations(source_id);
                CREATE INDEX IF NOT EXISTS idx_kg_relations_target 
                    ON kg_relations(target_id);
                CREATE INDEX IF NOT EXISTS idx_kg_relations_type 
                    ON kg_relations(relation_type);
            """)

    def add_entity(self, entity: Entity) -> None:
        if self._conn is None:
            raise KnowledgeGraphError("Database unavailable")
        with self._conn.cursor() as cur:
            cur.execute("""
                INSERT INTO kg_entities (id, name, entity_type, metadata)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    entity_type = EXCLUDED.entity_type,
                    metadata = EXCLUDED.metadata,
                    updated_at = NOW()
            """, (
                entity.id,
                entity.name,
                entity.entity_type,
                psycopg2.extras.Json(entity.metadata),
            ))

    def add_relation(self, relation: Relation) -> None:
        if self._conn is None:
            raise KnowledgeGraphError("Database unavailable")
        with self._conn.cursor() as cur:
            cur.execute("""
                INSERT INTO kg_relations (source_id, target_id, relation_type, metadata)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (source_id, target_id, relation_type) DO UPDATE SET
                    metadata = EXCLUDED.metadata
            """, (
                relation.source_id,
                relation.target_id,
                relation.relation_type,
                psycopg2.extras.Json(relation.metadata),
            ))

    def query(self, query: GraphQuery) -> GraphResult:
        if self._conn is None:
            raise KnowledgeGraphError("Database unavailable")

        import time
        start = time.perf_counter()

        with self._conn.cursor() as cur:
            # Build recursive CTE for traversal
            params: list[Any] = []
            where_clauses = []

            if query.entity_name:
                where_clauses.append("e.name ILIKE %s")
                params.append(f"%{query.entity_name}%")
            if query.entity_type:
                where_clauses.append("e.entity_type = %s")
                params.append(query.entity_type)

            where_str = " AND ".join(where_clauses) if where_clauses else "TRUE"

            cur.execute(f"""
                WITH RECURSIVE traversal AS (
                    -- Seed: matching entities
                    SELECT e.id, e.name, e.entity_type, e.metadata, 0 AS depth
                    FROM kg_entities e
                    WHERE {where_str}

                    UNION

                    -- Traverse relations
                    SELECT e.id, e.name, e.entity_type, e.metadata, t.depth + 1
                    FROM traversal t
                    JOIN kg_relations r ON (r.source_id = t.id OR r.target_id = t.id)
                    JOIN kg_entities e ON (
                        (r.source_id = t.id AND e.id = r.target_id) OR
                        (r.target_id = t.id AND e.id = r.source_id)
                    )
                    WHERE t.depth < %s
                )
                SELECT DISTINCT id, name, entity_type, metadata
                FROM traversal
                LIMIT %s
            """, (*params, query.depth, query.max_results))

            entity_rows = cur.fetchall()

            # Get relations between returned entities
            entity_ids = [row[0] for row in entity_rows]
            if entity_ids:
                cur.execute("""
                    SELECT source_id, target_id, relation_type, metadata
                    FROM kg_relations
                    WHERE source_id = ANY(%s) AND target_id = ANY(%s)
                """, (entity_ids, entity_ids))
                relation_rows = cur.fetchall()
            else:
                relation_rows = []

        entities = [
            Entity(
                id=row[0],
                name=row[1],
                entity_type=row[2],
                metadata=dict(row[3]) if row[3] else {},
            )
            for row in entity_rows
        ]

        relations = [
            Relation(
                source_id=row[0],
                target_id=row[1],
                relation_type=row[2],
                metadata=dict(row[3]) if row[3] else {},
            )
            for row in relation_rows
        ]

        return GraphResult(
            entities=entities,
            relations=relations,
            query_time_ms=(time.perf_counter() - start) * 1000,
        )

    def get_entity(self, entity_id: str) -> Entity | None:
        if self._conn is None:
            return None
        with self._conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, entity_type, metadata FROM kg_entities WHERE id = %s",
                (entity_id,),
            )
            row = cur.fetchone()
        if not row:
            return None
        return Entity(
            id=row[0],
            name=row[1],
            entity_type=row[2],
            metadata=dict(row[3]) if row[3] else {},
        )

    def delete_entity(self, entity_id: str) -> None:
        if self._conn is None:
            raise KnowledgeGraphError("Database unavailable")
        with self._conn.cursor() as cur:
            cur.execute("DELETE FROM kg_entities WHERE id = %s", (entity_id,))

    def health_check(self) -> bool:
        try:
            if self._conn:
                with self._conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    return cur.fetchone() is not None
        except Exception:
            pass
        return False
