"""The in-memory ``RecordStore`` fake — real object, no mocking.

A dict-backed ``RecordStore`` used wherever a test needs a store but not the
SQLite backing. It is a *verified* fake: the port contract suite
(``store_contract.py``) runs the same behavioural tests against this fake and the
real SQLite store, so the fake cannot drift from the contract undetected.
"""

from __future__ import annotations

from typing import override

from glyde.core import (
    DuplicateRecordError,
    Record,
    RecordStore,
    UnknownRecordError,
)


class InMemoryRecordStore(RecordStore):
    """A dict-backed ``RecordStore`` for tests."""

    def __init__(self) -> None:
        """Start empty."""
        self._records: dict[str, Record] = {}

    @override
    def add(self, record: Record) -> None:
        """Persist ``record``; raise ``DuplicateRecordError`` on an id clash."""
        if record.id in self._records:
            raise DuplicateRecordError
        self._records[record.id] = record

    @override
    def get(self, record_id: str) -> Record:
        """Return the record with ``record_id``; raise ``UnknownRecordError`` if absent."""
        try:
            return self._records[record_id]
        except KeyError as exc:
            raise UnknownRecordError from exc

    @override
    def list_all(self) -> list[Record]:
        """Return every record, ordered by ``created_at`` then ``id`` ascending."""
        return sorted(self._records.values(), key=lambda r: (r.created_at, r.id))
