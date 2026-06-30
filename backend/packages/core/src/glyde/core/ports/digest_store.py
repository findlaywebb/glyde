"""The ``DigestStore`` persistence port — the seam adapters implement.

Key types:
- ``DigestStore`` — the abstract persistence interface for ``Digest`` values and
  per-user ``Preferences``. Its method docstrings are the normative implementer
  contract; the SQLite adapter is written against them, and the in-memory test
  fake is kept honest by the port contract suite.

What this module does NOT do:
- No persistence of its own — it is the abstract seam. No clock reads, no id
  minting, no slug minting: a ``Digest`` arrives fully formed (id, slug, and
  timestamp already set by the api layer).

Invariants:
- Synchronous by design — FastAPI runs the sync store in its threadpool. The
  purity architecture test forbids ``async def`` in the adapters layer.
- ``add`` rejects a duplicate slug (``DuplicateSlugError``); ``get_by_slug``
  raises ``UnknownDigestError`` for an absent slug (never returns ``None``).
- ``list_all`` is newest-first; ``get_preferences`` returns the defaults for an
  ``owner_id`` that has none stored; ``put_preferences`` is an upsert.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from glyde.core.models import Digest, Preferences


class DigestStore(ABC):
    """Abstract persistence port for ``Digest`` values and ``Preferences``.

    Concrete adapters (e.g. the SQLite store) subclass this and implement every
    method against the contract stated here.
    """

    @abstractmethod
    def add(self, digest: Digest) -> None:
        """Persist ``digest``.

        Args:
            digest: A fully-formed digest (id, slug, and ``created_at`` already
                set by the api layer).

        Raises:
            DuplicateSlugError: If a digest with the same slug already exists.
        """

    @abstractmethod
    def get_by_slug(self, slug: str) -> Digest:
        """Return the digest with ``slug``.

        Args:
            slug: The memorable two-word slug to resolve.

        Returns:
            The stored ``Digest``.

        Raises:
            UnknownDigestError: If no digest has that slug.
        """

    @abstractmethod
    def list_all(self) -> list[Digest]:
        """Return every digest, newest-first (``created_at`` desc, then ``id``)."""

    @abstractmethod
    def get_preferences(self, owner_id: str) -> Preferences:
        """Return the preferences for ``owner_id``, or the defaults if none stored.

        Args:
            owner_id: The user whose preferences to read.

        Returns:
            The stored ``Preferences``, or a default ``Preferences`` (carrying
            the same ``owner_id``) when the user has none.
        """

    @abstractmethod
    def put_preferences(self, prefs: Preferences) -> None:
        """Upsert ``prefs`` by its ``owner_id`` (full-replace of the stored row)."""
