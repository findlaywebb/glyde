"""The durable ``RecordStore`` — SQLite (WAL) source of truth.

Key types:
- ``SqliteRecordStore`` — implements every ``RecordStore`` port method over a
  single ``sqlite3.Connection`` (one per request, opened via ``db.connect``).

What this module does NOT do:
- No schema management (the migration runner owns DDL), no connection lifecycle
  (the api layer's ``get_store`` opens and closes per request), no clock reads,
  no id minting — a ``Record`` arrives fully formed.

Invariants:
- Synchronous by design; the api layer runs it in FastAPI's threadpool.
- ``add`` maps a UNIQUE/primary-key clash to ``DuplicateRecordError``; ``get``
  raises ``UnknownRecordError`` for an absent id.
"""

from __future__ import annotations

import sqlite3
from typing import override

from glyde.core import (
    DuplicateRecordError,
    Record,
    RecordStore,
    UnknownRecordError,
)


class SqliteRecordStore(RecordStore):
    """A ``RecordStore`` backed by a single SQLite connection."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        """Bind the store to an already-opened connection.

        Args:
            conn: A connection from ``db.connect`` (pinned pragmas, row factory).
                The store does not own the connection's lifecycle.
        """
        self._conn = conn

    @override
    def add(self, record: Record) -> None:
        """Persist ``record``; raise ``DuplicateRecordError`` on an id clash."""
        try:
            self._conn.execute(
                "INSERT INTO records (id, name, created_at) VALUES (?, ?, ?)",
                (record.id, record.name, record.created_at),
            )
        except sqlite3.IntegrityError as exc:
            raise DuplicateRecordError from exc

    @override
    def get(self, record_id: str) -> Record:
        """Return the record with ``record_id``; raise ``UnknownRecordError`` if absent."""
        row = self._conn.execute(
            "SELECT id, name, created_at FROM records WHERE id = ?",
            (record_id,),
        ).fetchone()
        if row is None:
            raise UnknownRecordError
        return Record(id=row["id"], name=row["name"], created_at=row["created_at"])

    @override
    def list_all(self) -> list[Record]:
        """Return every record, ordered by ``created_at`` then ``id`` ascending."""
        rows = self._conn.execute(
            "SELECT id, name, created_at FROM records ORDER BY created_at, id"
        ).fetchall()
        return [
            Record(id=row["id"], name=row["name"], created_at=row["created_at"]) for row in rows
        ]
