"""The SQLite adapter: the durable store, its connection factory, and migrations.

Public surface:
- ``connect`` — the ONLY way to open this adapter's database (pinned pragmas).
- ``apply_migrations`` — bring a database file up to the newest migration.
- ``SqliteRecordStore`` — the durable ``RecordStore`` implementation.
"""

from glyde.adapters.sqlite.db import connect
from glyde.adapters.sqlite.migrate import apply_migrations
from glyde.adapters.sqlite.store import SqliteRecordStore

__all__ = ["SqliteRecordStore", "apply_migrations", "connect"]
