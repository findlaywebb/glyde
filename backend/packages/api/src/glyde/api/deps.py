"""Dependency providers wiring the api layer to the clock and the store.

Key callables:
- ``get_now`` — the clock as a FastAPI dependency: the single override point
  through which tests freeze time. Route handlers depend on this, never on
  ``clock`` directly, so ``app.dependency_overrides[get_now]`` reaches every
  route at once.
- ``get_store`` — a connection-per-request generator dependency: opens one
  SQLite connection, yields a ``SqliteRecordStore`` over it, and closes the
  connection in teardown. FastAPI runs the dependency, the handler, and the
  teardown as separate threadpool hops, which is why ``db.connect`` sets
  ``check_same_thread=False`` (sequential cross-thread, never concurrent).
- ``open_store`` — the one store-over-a-connection construction, shared by
  ``get_store`` (which re-yields it per request) and the CLI (which holds it
  for the whole command).
- ``bootstrap_migrations`` — bring the configured database up to date, stamping
  the backup filename with a digits-only UTC token. Used by the app lifespan
  and by the CLI before any work.

What this module does NOT do:
- No business logic — it only assembles the store and clock.
- No environment reads of its own — ``Settings`` owns those; this module takes
  a ``Settings`` (or resolves the cached one for the request dependency).

Invariants:
- One connection per request (``get_store``), closed in teardown; the CLI's
  ``open_store`` connection is closed on context-manager exit.
- The backup stamp passed to ``apply_migrations`` is digits-only UTC
  (``YYYYMMDDTHHMMSSZ``) — the canonical timestamp's colons and ``+`` violate
  the migration runner's filesystem-safe-token contract.
"""

from __future__ import annotations

from contextlib import closing, contextmanager
from datetime import datetime
from typing import TYPE_CHECKING, Annotated

from fastapi import Depends

from glyde.adapters.sqlite import SqliteRecordStore, apply_migrations, connect
from glyde.api.clock import canonical_now
from glyde.api.settings import Settings, get_settings

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path


def get_now() -> str:
    """Provide the server-stamped canonical timestamp for a request.

    The clock's single dependency seam: handlers depend on this, so a test can
    freeze time for every route through one ``app.dependency_overrides`` entry.

    Returns:
        The current canonical UTC timestamp string.
    """
    return canonical_now()


@contextmanager
def open_store(db_path: Path) -> Iterator[SqliteRecordStore]:
    """Yield a store over a fresh connection, closing it on exit.

    The one store-over-a-connection construction, shared by ``get_store`` (which
    re-yields it per request) and the CLI (which holds it for the whole command).
    """
    with closing(connect(db_path)) as conn:
        yield SqliteRecordStore(conn)


def get_store(
    settings: Annotated[Settings, Depends(get_settings)],
) -> Iterator[SqliteRecordStore]:
    """Yield a request-scoped store over a fresh connection, closed in teardown.

    A connection-per-request generator dependency: FastAPI runs the body up to
    the ``yield`` to provide the store, then the teardown after the response to
    close the connection. The database is assumed already migrated (the app
    lifespan runs migrations at startup). ``settings`` arrives via ``Depends`` so
    an ``app.dependency_overrides[get_settings]`` (the tmp-db test fixture) is
    honoured here.

    Yields:
        A ``SqliteRecordStore`` bound to a connection live for this request only.
    """
    with open_store(settings.db_path) as store:
        yield store


def _backup_stamp(now: str) -> str:
    """Derive a digits-only UTC backup token from a canonical timestamp.

    The migration runner embeds the stamp verbatim in a backup filename, so it
    must be filesystem-safe; the canonical form's colons and ``+`` are not. This
    reduces it to ``YYYYMMDDTHHMMSSZ``.

    Args:
        now: A canonical UTC timestamp string (``+00:00`` offset).

    Returns:
        The instant as ``YYYYMMDDTHHMMSSZ`` (digits, one ``T``, trailing ``Z``).
    """
    return datetime.fromisoformat(now).strftime("%Y%m%dT%H%M%SZ")


def bootstrap_migrations(settings: Settings) -> int:
    """Apply pending migrations to the configured database; return how many ran.

    Stamps the pre-migration backup filename with a digits-only UTC token.
    Called by the app lifespan at startup and by the CLI before any work, so both
    serving and in-process work run against a current schema.

    Args:
        settings: The runtime settings carrying the database path.

    Returns:
        The number of migrations applied (0 when the schema is already current).
    """
    return apply_migrations(settings.db_path, backup_stamp=_backup_stamp(canonical_now()))
