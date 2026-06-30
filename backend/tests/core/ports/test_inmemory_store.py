"""Run the digest store contract against the in-memory fake — keeping it honest."""

from typing import override

from support.memory_store import InMemoryDigestStore
from support.store_contract import DigestStoreContract

from glyde.core import DigestStore


class TestInMemoryDigestStore(DigestStoreContract):
    """The in-memory digest fake must satisfy the same contract as the real store."""

    @override
    def make_store(self) -> DigestStore:
        """Return a fresh in-memory digest store."""
        return InMemoryDigestStore()
