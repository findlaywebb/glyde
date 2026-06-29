"""Connection factory for the SQLite adapter: one connect path, pinned pragmas.

Key callables:
- ``connect`` — the ONLY way any code (store, migration runner, tests) opens
  this adapter's database. A single connect path is what makes the pragma
  guarantees hold everywhere; ``PRAGMA foreign_keys`` in particular is
  per-connection and never persisted, so a connection opened any other way
  silently loses foreign-key enforcement.

What this module does NOT do:
- No schema management — the migration runner owns DDL.
- No queries and no transactions — connections are returned in autocommit
  mode and callers manage transactions with explicit ``BEGIN``/``COMMIT``.

Invariants:
- ``autocommit=True``: no implicit transaction management. Pragmas execute
  outside any transaction (``journal_mode=WAL`` raises inside one), and
  transaction control is explicit SQL. In this mode
  ``Connection.commit()``/``.rollback()`` are inert no-ops — transactional
  callers must use ``conn.execute("COMMIT")`` / ``conn.execute("ROLLBACK")``.
- Pragmas on every connection: ``journal_mode=WAL``, ``synchronous=NORMAL``,
  ``foreign_keys=ON``, ``busy_timeout=5000`` (milliseconds).
- ``sqlite3.Row`` row factory: rows are read by column name, never by index.
- ``check_same_thread=False``: the connection may be used from a thread other
  than the one that opened it. This is safe ONLY because use is sequential
  cross-thread, never concurrent — the api layer opens one connection per
  request (``get_store``) and FastAPI runs the sync dependency, handler, and
  teardown as separate threadpool hops with no same-thread guarantee, but never
  two at once on the same connection. A genuinely concurrent caller would still
  need its own connection per thread.
"""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


def connect(db_path: Path) -> sqlite3.Connection:
    """Open the adapter's database with pinned pragmas and row factory.

    Creates the database file if it does not exist (SQLite semantics). The
    returned connection is in autocommit mode; see the module invariants for
    the transaction-control consequences.

    Args:
        db_path: Filesystem path of the database file.

    Returns:
        A connection with WAL journaling, NORMAL synchronous mode, per-
        connection foreign-key enforcement, a 5000 ms busy timeout,
        ``sqlite3.Row`` as the row factory, and ``check_same_thread=False``
        (sequential cross-thread use under connection-per-request).
    """
    conn = sqlite3.connect(db_path, autocommit=True, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn
