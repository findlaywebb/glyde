"""The port-contract suite — the behaviour every ``RecordStore`` must satisfy.

A test class mixes in ``RecordStoreContract`` and provides ``make_store()``; the
shared behavioural tests then run against that backing. Running the same suite
against the in-memory fake and the real SQLite store is what keeps the fake
honest (the verified-fake pattern): a fake that diverges from the contract fails
the suite, so tests built on it stay trustworthy.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import pytest

from glyde.core import DuplicateRecordError, RecordStore, UnknownRecordError
from support.factories import record


class RecordStoreContract(ABC):
    """Behavioural contract every ``RecordStore`` implementation must pass."""

    @abstractmethod
    def make_store(self) -> RecordStore:
        """Return a fresh, empty store of the implementation under test."""

    def test_add_then_get_round_trips(self) -> None:
        """A stored record is returned unchanged by get."""
        store = self.make_store()
        rec = record(id="a")
        store.add(rec)
        assert store.get("a") == rec

    def test_get_unknown_raises(self) -> None:
        """Get on an absent id raises UnknownRecordError, not None."""
        store = self.make_store()
        with pytest.raises(UnknownRecordError):
            store.get("missing")

    def test_duplicate_add_raises(self) -> None:
        """Adding a second record with an existing id raises DuplicateRecordError."""
        store = self.make_store()
        store.add(record(id="a"))
        with pytest.raises(DuplicateRecordError):
            store.add(record(id="a", name="other"))

    def test_list_all_orders_by_created_at(self) -> None:
        """Return records ordered by created_at ascending (list_all)."""
        store = self.make_store()
        store.add(record(id="b", created_at="2025-01-02T00:00:00+00:00"))
        store.add(record(id="a", created_at="2025-01-01T00:00:00+00:00"))
        assert [r.id for r in store.list_all()] == ["a", "b"]
