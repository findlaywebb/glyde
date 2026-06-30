"""Run the store contracts against the real SQLite stores + full-fidelity round-trips."""

from collections.abc import Iterator
from contextlib import closing
from typing import override

import pytest
from support.factories import block, pause, prose, provenance, ts
from support.store_contract import DigestStoreContract, RecordStoreContract

from glyde.adapters.sqlite import (
    SqliteDigestStore,
    SqliteRecordStore,
    apply_migrations,
    connect,
)
from glyde.core import Digest, DigestMeta, DigestStore, ReadingHint, RecordStore


class _MigratedDb:
    """Mixin providing a migrated tmp database and an open connection per test."""

    @pytest.fixture(autouse=True)
    def _db(self, tmp_path) -> Iterator[None]:
        """Migrate a fresh tmp database and hold an open connection for the test."""
        db_path = tmp_path / "test.db"
        apply_migrations(db_path, backup_stamp="00000000T000000Z")
        # closing(), not a bare `with connect()`: a sqlite3.Connection used as a context
        # manager commits/rolls back on exit but does NOT close — leaving it open trips the
        # ResourceWarning, which filterwarnings=error turns into a failure.
        with closing(connect(db_path)) as conn:
            self._conn = conn
            yield


class TestSqliteDigestStore(_MigratedDb, DigestStoreContract):
    """The SQLite digest store must satisfy the contract end to end against a real file db."""

    @override
    def make_store(self) -> DigestStore:
        """Return a store over the migrated tmp database."""
        return SqliteDigestStore(self._conn)

    def test_round_trips_every_segment_kind_and_metadata(self) -> None:
        """A digest with all segment kinds, tags, and a reading hint survives a round-trip."""
        store = SqliteDigestStore(self._conn)
        meta = DigestMeta(
            id="rich-1",
            slug="rich-otter",
            name="rich",
            provenance=provenance(source_kind="agent", origin="run-42"),
            created_at=ts(),
            token_count=2,
            est_reading_ms=400,
            content_sha="a" * 64,
            tags=["pr", "review"],
            reading_hint=ReadingHint(suggested_mode="rsvp"),
        )
        rich = Digest(
            meta=meta,
            segments=[
                prose("Run", "this", role="body"),
                pause("block_ahead"),
                block("code", content="x = 1", lead="Run this"),
                block("table", content="| a | b |"),
                block("image", content="cat.png"),
                block("quote", content="wisdom"),
                block("math", content="E=mc^2"),
                block("note", content="breathe"),
            ],
        )
        store.add(rich)
        assert store.get_by_slug("rich-otter") == rich


class TestSqliteRecordStore(_MigratedDb, RecordStoreContract):
    """The SQLite record store must satisfy the contract end to end (transitional)."""

    @override
    def make_store(self) -> RecordStore:
        """Return a record store over the migrated tmp database."""
        return SqliteRecordStore(self._conn)
