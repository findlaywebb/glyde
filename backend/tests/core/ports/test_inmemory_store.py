"""Run the store contract against the in-memory fake — keeping the fake honest."""

from typing import override

from support.memory_store import InMemoryRecordStore
from support.store_contract import RecordStoreContract

from glyde.core import RecordStore


class TestInMemoryStore(RecordStoreContract):
    """The in-memory fake must satisfy the same contract as the real store."""

    @override
    def make_store(self) -> RecordStore:
        """Return a fresh in-memory store."""
        return InMemoryRecordStore()
