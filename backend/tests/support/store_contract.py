"""The port-contract suites — the behaviour every store implementation must satisfy.

A test class mixes in a contract and provides ``make_store()``; the shared
behavioural tests then run against that backing. Running the same suite against
the in-memory fake and the real SQLite store is what keeps the fake honest (the
verified-fake pattern): a fake that diverges from the contract fails the suite,
so tests built on it stay trustworthy.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import pytest

from glyde.core import (
    DigestStore,
    DuplicateRecordError,
    DuplicateSlugError,
    RecordStore,
    UnknownDigestError,
    UnknownRecordError,
)
from support.factories import digest, preferences, record


class DigestStoreContract(ABC):
    """Behavioural contract every ``DigestStore`` implementation must pass."""

    @abstractmethod
    def make_store(self) -> DigestStore:
        """Return a fresh, empty store of the implementation under test."""

    def test_add_then_get_by_slug_round_trips(self) -> None:
        """A stored digest is returned unchanged by its slug."""
        store = self.make_store()
        dig = digest(slug="brave-otter")
        store.add(dig)
        assert store.get_by_slug("brave-otter") == dig

    def test_get_unknown_slug_raises(self) -> None:
        """get_by_slug on an absent slug raises UnknownDigestError, not None."""
        store = self.make_store()
        with pytest.raises(UnknownDigestError):
            store.get_by_slug("missing-slug")

    def test_duplicate_slug_add_raises(self) -> None:
        """Adding a second digest with an existing slug raises DuplicateSlugError."""
        store = self.make_store()
        store.add(digest(id="a", slug="dup-slug"))
        with pytest.raises(DuplicateSlugError):
            store.add(digest(id="b", slug="dup-slug", name="other"))

    def test_list_all_is_newest_first(self) -> None:
        """list_all orders digests by created_at descending (newest first)."""
        store = self.make_store()
        store.add(digest(id="a", slug="older", created_at="2025-01-01T00:00:00+00:00"))
        store.add(digest(id="b", slug="newer", created_at="2025-01-02T00:00:00+00:00"))
        assert [d.meta.slug for d in store.list_all()] == ["newer", "older"]

    def test_get_preferences_returns_defaults_for_unknown_owner(self) -> None:
        """get_preferences returns a default Preferences (guided) for an unknown owner."""
        store = self.make_store()
        prefs = store.get_preferences("nobody")
        assert (prefs.owner_id, prefs.mode) == ("nobody", "guided")

    def test_put_then_get_preferences_round_trips(self) -> None:
        """Stored preferences are read back by owner_id."""
        store = self.make_store()
        store.put_preferences(preferences(owner_id="local", mode="rsvp"))
        assert store.get_preferences("local").mode == "rsvp"

    def test_put_preferences_upserts(self) -> None:
        """A second put for the same owner replaces the stored preferences."""
        store = self.make_store()
        store.put_preferences(preferences(owner_id="local", mode="rsvp"))
        store.put_preferences(preferences(owner_id="local", mode="fading"))
        assert store.get_preferences("local").mode == "fading"


class RecordStoreContract(ABC):
    """Behavioural contract every ``RecordStore`` implementation must pass (transitional)."""

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
