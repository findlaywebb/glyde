"""The durable ``DigestStore`` — SQLite (WAL) source of truth.

Key types:
- ``SqliteDigestStore`` — implements every ``DigestStore`` port method over a
  single ``sqlite3.Connection`` (one per request, opened via ``db.connect``).

The store serialises a digest's metadata into typed columns and its ``segments``
timeline as one JSON blob (``model_dump_json`` out, ``model_validate_json`` in) —
no per-segment row joins. ``Preferences`` are a single JSON blob keyed by
``owner_id``.

What this module does NOT do:
- No schema management (the migration runner owns DDL), no connection lifecycle
  (the api layer's ``get_digest_store`` opens and closes per request), no clock
  reads, no id/slug minting — a ``Digest`` arrives fully formed.

Invariants:
- Synchronous by design; the api layer runs it in FastAPI's threadpool.
- ``add`` maps a UNIQUE-slug clash to ``DuplicateSlugError``; ``get_by_slug``
  raises ``UnknownDigestError`` for an absent slug. ``list_all`` is newest-first
  (``created_at`` desc, then ``id`` desc).
"""

from __future__ import annotations

import json
import sqlite3
from typing import TYPE_CHECKING, override

from pydantic import TypeAdapter

from glyde.core import (
    Digest,
    DigestMeta,
    DigestStore,
    DuplicateSlugError,
    Preferences,
    Provenance,
    ReadingHint,
    Segment,
    UnknownDigestError,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

_SEGMENTS = TypeAdapter(list[Segment])

_INSERT = """
INSERT INTO digests (
  id, slug, name, prov_source_kind, prov_origin, prov_producer, prov_ingested_via,
  prov_enriched, created_at, token_count, est_reading_ms, content_sha, ir_version,
  owner_id, tags, reading_hint, segments
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

_UPSERT_PREFS = """
INSERT INTO preferences (owner_id, prefs) VALUES (?, ?)
ON CONFLICT(owner_id) DO UPDATE SET prefs = excluded.prefs
"""


def _insert_params(digest: Digest) -> tuple[object, ...]:
    """Flatten a digest into the positional row values the INSERT expects."""
    meta = digest.meta
    prov = meta.provenance
    hint = meta.reading_hint.model_dump_json() if meta.reading_hint is not None else None
    return (
        meta.id,
        meta.slug,
        meta.name,
        prov.source_kind,
        prov.origin,
        prov.producer,
        prov.ingested_via,
        int(prov.enriched),
        meta.created_at,
        meta.token_count,
        meta.est_reading_ms,
        meta.content_sha,
        meta.ir_version,
        meta.owner_id,
        json.dumps(meta.tags),
        hint,
        _SEGMENTS.dump_json(digest.segments).decode("utf-8"),
    )


def _row_to_digest(row: sqlite3.Row) -> Digest:
    """Rebuild a ``Digest`` from a ``digests`` row (typed columns + JSON blobs)."""
    hint = ReadingHint.model_validate_json(row["reading_hint"]) if row["reading_hint"] else None
    meta = DigestMeta(
        id=row["id"],
        slug=row["slug"],
        name=row["name"],
        provenance=Provenance(
            source_kind=row["prov_source_kind"],
            origin=row["prov_origin"],
            producer=row["prov_producer"],
            ingested_via=row["prov_ingested_via"],
            enriched=bool(row["prov_enriched"]),
        ),
        created_at=row["created_at"],
        token_count=row["token_count"],
        est_reading_ms=row["est_reading_ms"],
        content_sha=row["content_sha"],
        ir_version=row["ir_version"],
        owner_id=row["owner_id"],
        tags=json.loads(row["tags"]),
        reading_hint=hint,
    )
    return Digest(meta=meta, segments=_SEGMENTS.validate_json(row["segments"]))


class SqliteDigestStore(DigestStore):
    """A ``DigestStore`` backed by a single SQLite connection."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        """Bind the store to an already-opened connection.

        Args:
            conn: A connection from ``db.connect`` (pinned pragmas, row factory).
                The store does not own the connection's lifecycle.
        """
        self._conn = conn

    @override
    def add(self, digest: Digest) -> None:
        """Persist ``digest``; raise ``DuplicateSlugError`` on a slug clash."""
        try:
            self._conn.execute(_INSERT, _insert_params(digest))
        except sqlite3.IntegrityError as exc:
            raise DuplicateSlugError from exc

    @override
    def get_by_slug(self, slug: str) -> Digest:
        """Return the digest with ``slug``; raise ``UnknownDigestError`` if absent."""
        row = self._conn.execute("SELECT * FROM digests WHERE slug = ?", (slug,)).fetchone()
        if row is None:
            raise UnknownDigestError
        return _row_to_digest(row)

    @override
    def list_all(self) -> list[Digest]:
        """Return every digest, newest-first (``created_at`` desc, then ``id`` desc)."""
        rows: Sequence[sqlite3.Row] = self._conn.execute(
            "SELECT * FROM digests ORDER BY created_at DESC, id DESC"
        ).fetchall()
        return [_row_to_digest(row) for row in rows]

    @override
    def get_preferences(self, owner_id: str) -> Preferences:
        """Return stored preferences for ``owner_id``, else a default for them."""
        row = self._conn.execute(
            "SELECT prefs FROM preferences WHERE owner_id = ?", (owner_id,)
        ).fetchone()
        if row is None:
            return Preferences(owner_id=owner_id)
        return Preferences.model_validate_json(row["prefs"])

    @override
    def put_preferences(self, prefs: Preferences) -> None:
        """Upsert ``prefs`` by its ``owner_id`` (full-replace of the stored row)."""
        self._conn.execute(_UPSERT_PREFS, (prefs.owner_id, prefs.model_dump_json()))
