"""Port interfaces — the abstract seams concrete adapters implement.

A port is an abstract interface (ABC) that imports only from ``glyde.core``;
every concrete adapter in ``glyde.adapters`` must implement one, and the
architecture tests enforce that. This package re-exports the port surface:
``RecordStore`` (the example persistence port) and its error taxonomy.

Rule of three: new ports are NOT defined speculatively — each arrives here with
its first real consumer (prefer duplication over the wrong abstraction).
"""

from glyde.core.ports.errors import (
    DuplicateRecordError,
    StoreError,
    UnknownRecordError,
)
from glyde.core.ports.record_store import RecordStore

__all__ = [
    "DuplicateRecordError",
    "RecordStore",
    "StoreError",
    "UnknownRecordError",
]
