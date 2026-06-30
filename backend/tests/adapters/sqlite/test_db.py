"""Regression tests for the SQLite connect() path in db.py."""

from contextlib import closing
from pathlib import Path

from glyde.adapters.sqlite import apply_migrations, connect


class TestConnectCreatesParentDirectory:
    """connect() must create missing parent directories before opening the db."""

    def test_connect_creates_missing_parent_dirs(self, tmp_path: Path) -> None:
        """connect() with a db_path under a non-existent dir creates the dir and opens the db."""
        db_path = tmp_path / "a" / "b" / "c" / "glyde.db"
        assert not db_path.parent.exists()
        with closing(connect(db_path)) as conn:
            assert db_path.parent.exists()
            row = conn.execute("SELECT sqlite_version()").fetchone()
            assert row is not None

    def test_store_works_after_mkdir(self, tmp_path: Path) -> None:
        """A store opened via connect() on a freshly created dir survives a migration."""
        db_path = tmp_path / "deep" / "glyde.db"
        apply_migrations(db_path, backup_stamp="00000000T000000Z")
        with closing(connect(db_path)) as conn:
            version = conn.execute("PRAGMA user_version").fetchone()[0]
            assert isinstance(version, int)
            assert version > 0

    def test_connect_is_idempotent_when_dir_exists(self, tmp_path: Path) -> None:
        """connect() does not raise when the parent directory already exists."""
        db_path = tmp_path / "glyde.db"
        with closing(connect(db_path)) as conn:
            assert conn is not None
        with closing(connect(db_path)) as conn:
            assert conn is not None
