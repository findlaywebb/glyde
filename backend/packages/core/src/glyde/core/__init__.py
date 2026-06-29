"""Glyde's domain kernel: models, ports, and pure logic.

This layer owns the domain models, the port interfaces every adapter implements
(see ``glyde.core.ports``), and any pure logic. ``Record`` is the example
domain model that ships with the template — replace it with the real domain.

What it does NOT do: no I/O of any kind. No framework imports (FastAPI, DB
drivers, HTTP clients), no filesystem access, no ``os.environ`` — configuration
is injected by callers. Enforced by import-linter and the architecture tests,
not convention.

Invariants:
- Clock-free and id-free: core never reads the clock and never mints ids; both
  arrive as arguments (the api layer stamps time and mints ids).
- Timestamps are canonical ISO-8601 UTC strings; lexicographic order is
  therefore chronological order.
"""

from glyde.core.models import Record
from glyde.core.ports import (
    DuplicateRecordError,
    RecordStore,
    StoreError,
    UnknownRecordError,
)

__all__ = [
    "DuplicateRecordError",
    "Record",
    "RecordStore",
    "StoreError",
    "UnknownRecordError",
]
