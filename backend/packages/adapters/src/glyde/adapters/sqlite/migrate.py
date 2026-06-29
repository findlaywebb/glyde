"""Forward-only migration runner tracked by ``PRAGMA user_version``.

Key callables:
- ``apply_migrations`` — bring a database file up to the newest migration,
  taking a file-copy backup first when an existing schema is about to change.

What this module does NOT do:
- No down-migrations — recovery is the pre-migration backup file.
- No schema diffing or generation — migrations are hand-written SQL; the
  sibling ``schema.sql`` is a declarative anchor kept equal by a test, never
  executed here.
- No clock reads — the backup filename's timestamp arrives as an argument.

Invariants:
- Migrations are ``NNNN_*.sql`` files applied in ascending numeric order;
  exactly one file per number. A migration applies atomically: its script and
  its ``user_version`` bump share one explicit transaction, so a failed script
  leaves the database at the previous migration exactly.
- Migration scripts must contain NO explicit transaction control — the runner
  owns each migration's transaction, and an embedded ``COMMIT`` would silently
  break the atomicity above. Enforced: such a script is rejected whole
  (trigger-body ``BEGIN ... END`` stays legal; the words inside SQL string
  literals still trip the guard, loudly).
- The backup fires precisely when migrations are pending AND the database
  already has a schema (``user_version > 0``): fresh creates and no-op re-runs
  take none.
"""

from __future__ import annotations

import re
from contextlib import closing
from importlib.resources import files
from typing import TYPE_CHECKING

from glyde.adapters.sqlite.db import connect

if TYPE_CHECKING:
    import sqlite3
    from importlib.resources.abc import Traversable
    from pathlib import Path

_MIGRATION_NAME = re.compile(r"^(\d{4})_.+\.sql$")

# The runner owns each migration's transaction; a script smuggling its own
# BEGIN/COMMIT/ROLLBACK would silently break per-migration atomicity (under
# autocommit, executescript would commit the runner's open transaction).
# BEGIN is matched only in its transaction forms so trigger-body BEGIN...END
# stays legal; COMMIT/ROLLBACK are illegal in trigger bodies anyway. Known
# limit: the words inside SQL string literals still false-positive (loudly).
_TXN_CONTROL = re.compile(
    r"\bBEGIN\s*(;|TRANSACTION|DEFERRED|IMMEDIATE|EXCLUSIVE)\b|\b(COMMIT|ROLLBACK)\b",
    re.IGNORECASE,
)
_SQL_COMMENT = re.compile(r"--[^\n]*|/\*.*?\*/", re.DOTALL)


def _require_no_txn_control(number: int, sql: str) -> None:
    """Reject a migration script that carries explicit transaction control.

    Raises:
        ValueError: If the comment-stripped script contains BEGIN, COMMIT, or
            ROLLBACK — the runner owns the transaction.
    """
    if _TXN_CONTROL.search(_SQL_COMMENT.sub("", sql)):
        msg = (
            f"Migration {number:04d} contains explicit transaction control "
            "(BEGIN/COMMIT/ROLLBACK); the runner owns each migration's transaction."
        )
        raise ValueError(msg)


def _discover(source: Path | Traversable) -> list[tuple[int, Traversable | Path]]:
    """Return ``(number, file)`` pairs for every migration in ``source``, ascending.

    Raises:
        ValueError: If two files claim the same migration number, or a file
            claims number 0000 (never pending — fresh databases start there).
    """
    found: dict[int, Traversable | Path] = {}
    for entry in source.iterdir():
        match = _MIGRATION_NAME.match(entry.name)
        if match is None:
            continue
        number = int(match.group(1))
        if number == 0:
            msg = (
                f"Migration number 0000 ({entry.name!r}) can never be pending — "
                "a fresh database starts at user_version 0; number from 0001."
            )
            raise ValueError(msg)
        if number in found:
            msg = (
                f"Duplicate migration number {number:04d}: "
                f"{found[number].name!r} and {entry.name!r}."
            )
            raise ValueError(msg)
        found[number] = entry
    return sorted(found.items())


def _backup(conn: sqlite3.Connection, db_path: Path, version: int, stamp: str) -> None:
    """Copy the live database to the pinned-name sibling via the backup API."""
    target_path = db_path.with_name(f"{db_path.name}.v{version}.{stamp}.bak")
    with closing(connect(target_path)) as target:
        conn.backup(target)


def apply_migrations(
    db_path: Path,
    *,
    backup_stamp: str,
    source: Path | Traversable | None = None,
) -> int:
    """Apply every pending migration to ``db_path``; return how many applied.

    Pending means a migration number greater than the database's current
    ``PRAGMA user_version``. Each migration runs atomically (script plus
    version bump in one transaction). When the database already has a schema
    and migrations are pending, the file is first copied to
    ``{name}.v{current_version}.{backup_stamp}.bak`` beside it.

    Args:
        db_path: Database file; created if absent (a fresh install).
        backup_stamp: Filesystem-safe token included verbatim in the backup
            filename — typically a timestamp, stamped by the caller because
            this adapter never reads the clock.
        source: Directory holding ``NNNN_*.sql`` files; defaults to the
            packaged migrations.

    Returns:
        The number of migrations applied (0 = nothing was pending).

    Raises:
        ValueError: If two source files claim the same migration number.
        sqlite3.Error: From a failing migration script, after its rollback.
    """
    if source is None:
        source = files("glyde.adapters.sqlite") / "migrations"
    with closing(connect(db_path)) as conn:
        current: int = conn.execute("PRAGMA user_version").fetchone()[0]
        pending = [(number, entry) for number, entry in _discover(source) if number > current]
        if pending and current > 0:
            _backup(conn, db_path, current, backup_stamp)
        for number, entry in pending:
            script = entry.read_text()
            _require_no_txn_control(number, script)
            conn.execute("BEGIN")
            try:
                conn.executescript(script)
                conn.execute(f"PRAGMA user_version = {number:d}")
                conn.execute("COMMIT")
            except BaseException:
                conn.execute("ROLLBACK")
                raise
        return len(pending)
