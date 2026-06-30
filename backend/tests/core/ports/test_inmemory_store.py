"""Run the store contracts against the in-memory fakes — keeping the fakes honest."""

from typing import override

from support.memory_store import InMemoryDigestStore, InMemoryRecordStore
from support.store_contract import DigestStoreContract, RecordStoreContract

from glyde.core import DigestStore, RecordStore


class TestInMemoryDigestStore(DigestStoreContract):
    """The in-memory digest fake must satisfy the same contract as the real store."""

    @override
    def make_store(self) -> DigestStore:
        """Return a fresh in-memory digest store."""
        return InMemoryDigestStore()


class TestInMemoryRecordStore(RecordStoreContract):
    """The in-memory record fake must satisfy the same contract as the real store."""

    @override
    def make_store(self) -> RecordStore:
        """Return a fresh in-memory record store."""
        return InMemoryRecordStore()
