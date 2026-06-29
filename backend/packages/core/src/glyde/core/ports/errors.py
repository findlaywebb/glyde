"""Error taxonomy for the store ports.

Every store-rejection condition is a typed exception carrying a machine-readable
``code`` (a ``ClassVar[str]``). The api layer maps these codes onto its HTTP
rejection body — the code, not the Python class, is the stable contract across
the api boundary.

Key types:
- ``StoreError`` — the base; ``except StoreError`` catches every store-raised
  rejection, and ``error.code`` is always defined.
- One subclass per rejection condition, each with a distinct ``code``.

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


class UnknownRecordError(StoreError):
    """A record id is absent from the store.

    Raised by reads or writes targeting an id the store has never persisted.
    """

    code: ClassVar[str] = "unknown_record"


class DuplicateRecordError(StoreError):
    """A record id already exists.

    Raised by ``add`` when its ``record.id`` is already present.
    """

    code: ClassVar[str] = "duplicate_record"
