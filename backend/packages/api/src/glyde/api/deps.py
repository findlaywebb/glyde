"""Dependency providers wiring the api layer to the clock and the digest store.

Key callables:
- ``get_now`` — the clock as a FastAPI dependency: the single override point
  through which tests freeze time.
- ``get_digest_store`` — a connection-per-request generator dependency: opens one
  SQLite connection, yields a ``SqliteDigestStore`` over it, and closes it in
  teardown.
- ``open_digest_store`` — the one store-over-a-connection construction, shared by
  the request dependency and the CLI (which holds it for the whole command).
- ``bootstrap_migrations`` — bring the configured database up to date, stamping
  the backup filename with a digits-only UTC token.

What this module does NOT do:
- No business logic — it only assembles the store and clock.
- No environment reads of its own — ``Settings`` owns those.

Invariants:
- One connection per request, closed in teardown; the CLI's ``open_digest_store``
  connection is closed on context-manager exit.
- The backup stamp passed to ``apply_migrations`` is digits-only UTC
  (``YYYYMMDDTHHMMSSZ``) — the canonical timestamp's colons and ``+`` violate the
  migration runner's filesystem-safe-token contract.
"""

from __future__ import annotations

from contextlib import closing, contextmanager
from datetime import datetime
from typing import TYPE_CHECKING, Annotated

from fastapi import Depends

from glyde.adapters.sqlite import SqliteDigestStore, apply_migrations, connect
from glyde.api.clock import canonical_now
from glyde.api.settings import Settings, get_settings

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path


def get_now() -> str:
    """Provide the server-stamped canonical timestamp for a request.

    Returns:
        The current canonical UTC timestamp string.
    """
    return canonical_now()


@contextmanager
def open_digest_store(db_path: Path) -> Iterator[SqliteDigestStore]:
    """Yield a digest store over a fresh connection, closing it on exit."""
    with closing(connect(db_path)) as conn:
        yield SqliteDigestStore(conn)


def get_digest_store(
    settings: Annotated[Settings, Depends(get_settings)],
) -> Iterator[SqliteDigestStore]:
    """Yield a request-scoped digest store over a fresh connection, closed in teardown.

    The database is assumed already migrated (the app lifespan runs migrations at
    startup). ``settings`` arrives via ``Depends`` so a tmp-db test override is
    honoured.

    Yields:
        A ``SqliteDigestStore`` bound to a connection live for this request only.
    """
    with open_digest_store(settings.db_path) as store:
        yield store


def _backup_stamp(now: str) -> str:
    """Derive a digits-only UTC backup token (``YYYYMMDDTHHMMSSZ``) from ``now``."""
    return datetime.fromisoformat(now).strftime("%Y%m%dT%H%M%SZ")


def bootstrap_migrations(settings: Settings) -> int:
    """Apply pending migrations to the configured database; return how many ran.

    Args:
        settings: The runtime settings carrying the database path.

    Returns:
        The number of migrations applied (0 when the schema is already current).
    """
    return apply_migrations(settings.db_path, backup_stamp=_backup_stamp(canonical_now()))
