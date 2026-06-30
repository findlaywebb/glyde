"""In-memory digest store fake — a real object, no mocking.

A dict-backed ``DigestStore`` used wherever a test needs a store but not the
SQLite backing. It is a *verified* fake: the port contract suite
(``store_contract.py``) runs the same behavioural tests against this fake and the
real SQLite store, so the fake cannot drift from the contract undetected.
"""

from __future__ import annotations

from typing import override

from glyde.core import (
    Digest,
    DigestStore,
    DuplicateSlugError,
    Preferences,
    UnknownDigestError,
)


class InMemoryDigestStore(DigestStore):
    """A dict-backed ``DigestStore`` for tests (digests keyed by slug)."""

    def __init__(self) -> None:
        """Start empty."""
        self._digests: dict[str, Digest] = {}
        self._prefs: dict[str, Preferences] = {}

    @override
    def add(self, digest: Digest) -> None:
        """Persist ``digest``; raise ``DuplicateSlugError`` on a slug clash."""
        if digest.meta.slug in self._digests:
            raise DuplicateSlugError
        self._digests[digest.meta.slug] = digest

    @override
    def get_by_slug(self, slug: str) -> Digest:
        """Return the digest with ``slug``; raise ``UnknownDigestError`` if absent."""
        try:
            return self._digests[slug]
        except KeyError as exc:
            raise UnknownDigestError from exc

    @override
    def list_all(self) -> list[Digest]:
        """Return every digest, newest-first (``created_at`` desc, then ``id`` desc)."""
        return sorted(
            self._digests.values(),
            key=lambda d: (d.meta.created_at, d.meta.id),
            reverse=True,
        )

    @override
    def get_preferences(self, owner_id: str) -> Preferences:
        """Return stored preferences for ``owner_id``, else a default for them."""
        return self._prefs.get(owner_id, Preferences(owner_id=owner_id))

    @override
    def put_preferences(self, prefs: Preferences) -> None:
        """Upsert ``prefs`` by its ``owner_id``."""
        self._prefs[prefs.owner_id] = prefs
