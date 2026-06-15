from __future__ import annotations

import json
import math
import sqlite3
from collections import Counter
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from omega.schema import MemoryKind, MemoryRecord, TaskResult


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _tokenize(text: str) -> list[str]:
    return [token.lower() for token in "".join(ch if ch.isalnum() else " " for ch in text).split()]


def _hash_embedding(text: str, dimensions: int = 128) -> list[float]:
    counts = Counter(_tokenize(text))
    vector = [0.0] * dimensions
    for token, count in counts.items():
        vector[hash(token) % dimensions] += float(count)
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / norm for value in vector]


def _cosine(left: Iterable[float], right: Iterable[float]) -> float:
    return sum(a * b for a, b in zip(left, right, strict=False))


class MemoryStore:
    """Persistent memory, task history, and lightweight knowledge graph backed by SQLite."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        self.initialize()

    def initialize(self) -> None:
        self.connection.executescript(
            """
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS memory_records (
                id TEXT PRIMARY KEY,
                kind TEXT NOT NULL,
                content TEXT NOT NULL,
                tags TEXT NOT NULL,
                metadata TEXT NOT NULL,
                importance REAL NOT NULL,
                embedding TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_memory_kind_created ON memory_records(kind, created_at);

            CREATE TABLE IF NOT EXISTS task_results (
                task_id TEXT PRIMARY KEY,
                agent TEXT NOT NULL,
                status TEXT NOT NULL,
                summary TEXT NOT NULL,
                artifacts TEXT NOT NULL,
                messages TEXT NOT NULL,
                started_at TEXT NOT NULL,
                finished_at TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS graph_nodes (
                id TEXT PRIMARY KEY,
                kind TEXT NOT NULL,
                name TEXT NOT NULL,
                metadata TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE UNIQUE INDEX IF NOT EXISTS idx_graph_node_kind_name ON graph_nodes(kind, name);

            CREATE TABLE IF NOT EXISTS graph_edges (
                id TEXT PRIMARY KEY,
                source_id TEXT NOT NULL,
                relation TEXT NOT NULL,
                target_id TEXT NOT NULL,
                metadata TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(source_id, relation, target_id)
            );
            """
        )
        self.connection.commit()

    def add(self, record: MemoryRecord) -> MemoryRecord:
        embedding = _hash_embedding(" ".join([record.content, *record.tags]))
        self.connection.execute(
            """
            INSERT OR REPLACE INTO memory_records
            (id, kind, content, tags, metadata, importance, embedding, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.id,
                record.kind.value,
                record.content,
                json.dumps(record.tags),
                json.dumps(record.metadata),
                record.importance,
                json.dumps(embedding),
                record.created_at.isoformat(),
            ),
        )
        self.connection.commit()
        return record

    def remember(
        self,
        content: str,
        *,
        kind: MemoryKind = MemoryKind.LONG_TERM,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        importance: float = 0.5,
    ) -> MemoryRecord:
        return self.add(
            MemoryRecord(
                kind=kind,
                content=content,
                tags=tags or [],
                metadata=metadata or {},
                importance=importance,
            )
        )

    def get(self, record_id: str) -> MemoryRecord | None:
        row = self.connection.execute(
            "SELECT * FROM memory_records WHERE id = ?",
            (record_id,),
        ).fetchone()
        return self._row_to_memory(row) if row else None

    def recent(self, *, kind: MemoryKind | None = None, limit: int = 20) -> list[MemoryRecord]:
        if kind:
            rows = self.connection.execute(
                "SELECT * FROM memory_records WHERE kind = ? ORDER BY created_at DESC LIMIT ?",
                (kind.value, limit),
            ).fetchall()
        else:
            rows = self.connection.execute(
                "SELECT * FROM memory_records ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [self._row_to_memory(row) for row in rows]

    def search(
        self,
        query: str,
        *,
        kind: MemoryKind | None = None,
        limit: int = 10,
    ) -> list[tuple[MemoryRecord, float]]:
        query_embedding = _hash_embedding(query)
        query_tokens = set(_tokenize(query))
        if kind:
            rows = self.connection.execute(
                "SELECT * FROM memory_records WHERE kind = ?",
                (kind.value,),
            ).fetchall()
        else:
            rows = self.connection.execute("SELECT * FROM memory_records").fetchall()

        scored: list[tuple[MemoryRecord, float]] = []
        for row in rows:
            record = self._row_to_memory(row)
            embedding = json.loads(row["embedding"])
            lexical = len(query_tokens.intersection(_tokenize(record.content))) / max(len(query_tokens), 1)
            tag_bonus = 0.15 * len(query_tokens.intersection({tag.lower() for tag in record.tags}))
            score = _cosine(query_embedding, embedding) + lexical + tag_bonus + record.importance * 0.05
            if score > 0:
                scored.append((record, score))
        scored.sort(key=lambda item: item[1], reverse=True)
        return scored[:limit]

    def add_task_result(self, result: TaskResult) -> None:
        self.connection.execute(
            """
            INSERT OR REPLACE INTO task_results
            (task_id, agent, status, summary, artifacts, messages, started_at, finished_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                result.task_id,
                result.agent,
                result.status.value,
                result.summary,
                json.dumps(result.artifacts),
                json.dumps([message.model_dump() for message in result.messages]),
                result.started_at.isoformat(),
                result.finished_at.isoformat(),
                _utc_now(),
            ),
        )
        self.connection.commit()

    def task_history(self, limit: int = 20) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            "SELECT * FROM task_results ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]

    def upsert_node(self, *, node_id: str, kind: str, name: str, metadata: dict[str, Any] | None = None) -> str:
        self.connection.execute(
            """
            INSERT INTO graph_nodes (id, kind, name, metadata, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(kind, name) DO UPDATE SET metadata = excluded.metadata, updated_at = excluded.updated_at
            """,
            (node_id, kind, name, json.dumps(metadata or {}), _utc_now()),
        )
        self.connection.commit()
        row = self.connection.execute(
            "SELECT id FROM graph_nodes WHERE kind = ? AND name = ?",
            (kind, name),
        ).fetchone()
        return str(row["id"])

    def link_nodes(
        self,
        *,
        edge_id: str,
        source_id: str,
        relation: str,
        target_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        self.connection.execute(
            """
            INSERT INTO graph_edges (id, source_id, relation, target_id, metadata, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(source_id, relation, target_id)
            DO UPDATE SET metadata = excluded.metadata, updated_at = excluded.updated_at
            """,
            (edge_id, source_id, relation, target_id, json.dumps(metadata or {}), _utc_now()),
        )
        self.connection.commit()
        row = self.connection.execute(
            "SELECT id FROM graph_edges WHERE source_id = ? AND relation = ? AND target_id = ?",
            (source_id, relation, target_id),
        ).fetchone()
        return str(row["id"])

    def graph_neighbors(self, node_id: str) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            """
            SELECT e.relation, e.metadata AS edge_metadata, n.id, n.kind, n.name, n.metadata AS node_metadata
            FROM graph_edges e
            JOIN graph_nodes n ON n.id = e.target_id
            WHERE e.source_id = ?
            ORDER BY e.updated_at DESC
            """,
            (node_id,),
        ).fetchall()
        return [dict(row) for row in rows]

    def close(self) -> None:
        self.connection.close()

    def _row_to_memory(self, row: sqlite3.Row) -> MemoryRecord:
        return MemoryRecord(
            id=row["id"],
            kind=MemoryKind(row["kind"]),
            content=row["content"],
            tags=json.loads(row["tags"]),
            metadata=json.loads(row["metadata"]),
            importance=float(row["importance"]),
            created_at=datetime.fromisoformat(row["created_at"]),
        )
