"""The ``RecordStore`` persistence port — the example seam adapters implement.

Key types:
- ``RecordStore`` — the abstract persistence interface for ``Record`` values. Its
  method docstrings are the normative implementer contract; the SQLite adapter is
  written against them, and the in-memory test fake is kept honest by the port
  contract suite.

What this module does NOT do:
- No persistence of its own — it is the abstract seam. No clock reads, no id
  minting: a ``Record`` arrives fully formed (id and timestamp already set by the
  api layer).

Invariants:
- Synchronous by design — FastAPI runs the sync store in its threadpool. The
  purity architecture test forbids ``async def`` in the adapters layer.
- ``add`` rejects a duplicate id (``DuplicateRecordError``); ``get`` raises
  ``UnknownRecordError`` for an absent id (it does not return ``None``).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from glyde.core.models import Record


class RecordStore(ABC):
    """Abstract persistence port for ``Record`` values.

    Concrete adapters (e.g. the SQLite store) subclass this and implement every
    method against the contract stated here.
    """

    @abstractmethod
    def add(self, record: Record) -> None:
        """Persist ``record``.

        Args:
            record: A fully-formed record (id and ``created_at`` already set by
                the api layer).

        Raises:
            DuplicateRecordError: If a record with the same id already exists.
        """

    @abstractmethod
    def get(self, record_id: str) -> Record:
        """Return the record with ``record_id``.

        Args:
            record_id: The id to look up.

        Returns:
            The stored ``Record``.

        Raises:
            UnknownRecordError: If no record has that id.
        """

    @abstractmethod
    def list_all(self) -> list[Record]:
        """Return every stored record, ordered by ``created_at`` ascending."""
