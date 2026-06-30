"""Error taxonomy for the digest store port.

Every store-rejection condition is a typed exception carrying a machine-readable
``code`` (a ``ClassVar[str]``). The api layer maps these codes onto its HTTP
rejection body — the code, not the Python class, is the stable contract across
the api boundary.

Key types:
- ``StoreError`` — the base; ``except StoreError`` catches every store-raised
  rejection, and ``error.code`` is always defined.
- ``UnknownDigestError`` / ``DuplicateSlugError`` — the digest store rejections.

What this module does NOT do:
- No I/O, no mapping to HTTP status — that translation is the api layer's job.

Invariants:
- Every concrete subclass sets ``code`` to a unique, stable, snake_case string.
- Codes are part of the port contract; renaming one is an ADR-level change.
"""

from __future__ import annotations

from typing import ClassVar


class StoreError(Exception):
    """Base for every store rejection.

    Carries a machine-readable ``code`` that the api layer maps onto its
    rejection vocabulary. Catch this base to handle any store rejection; read
    ``code`` to branch on the specific condition.
    """

    code: ClassVar[str] = "store_error"


class UnknownDigestError(StoreError):
    """A digest slug is absent from the store.

    Raised by ``get_by_slug`` for a slug the store has never persisted (it
    raises, never returns ``None``).
    """

    code: ClassVar[str] = "unknown_digest"


class DuplicateSlugError(StoreError):
    """A digest slug already exists.

    Raised by ``add`` when its ``digest.meta.slug`` is already present (the slug
    is the secondary unique key, 1:1 with the id).
    """

    code: ClassVar[str] = "duplicate_slug"
