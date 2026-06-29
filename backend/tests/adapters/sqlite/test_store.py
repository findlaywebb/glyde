"""Run the store contract against the real SQLite store."""

from collections.abc import Iterator
from contextlib import closing
from typing import override

import pytest
from support.store_contract import RecordStoreContract

from glyde.adapters.sqlite import SqliteRecordStore, apply_migrations, connect
from glyde.core import RecordStore


class TestSqliteStore(RecordStoreContract):
    """The SQLite store must satisfy the contract end to end against a real file db."""

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

    @override
    def make_store(self) -> RecordStore:
        """Return a store over the migrated tmp database."""
        return SqliteRecordStore(self._conn)
