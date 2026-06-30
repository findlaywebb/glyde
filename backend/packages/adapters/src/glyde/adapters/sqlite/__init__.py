"""The SQLite adapter: the durable stores, connection factory, and migrations.

Public surface:
- ``connect`` — the ONLY way to open this adapter's database (pinned pragmas).
- ``apply_migrations`` — bring a database file up to the newest migration.
- ``SqliteDigestStore`` — the durable ``DigestStore`` implementation.
- ``SqliteRecordStore`` — the template example store (transitional, removed once
  the Digest IR replaces it end to end).
"""

from glyde.adapters.sqlite.db import connect
from glyde.adapters.sqlite.digest_store import SqliteDigestStore
from glyde.adapters.sqlite.migrate import apply_migrations
from glyde.adapters.sqlite.store import SqliteRecordStore

__all__ = ["SqliteDigestStore", "SqliteRecordStore", "apply_migrations", "connect"]
