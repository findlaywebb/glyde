"""The SQLite adapter: the durable digest store, connection factory, migrations.

Public surface:
- ``connect`` — the ONLY way to open this adapter's database (pinned pragmas).
- ``apply_migrations`` — bring a database file up to the newest migration.
- ``SqliteDigestStore`` — the durable ``DigestStore`` implementation.
"""

from glyde.adapters.sqlite.db import connect
from glyde.adapters.sqlite.digest_store import SqliteDigestStore
from glyde.adapters.sqlite.migrate import apply_migrations

__all__ = ["SqliteDigestStore", "apply_migrations", "connect"]
