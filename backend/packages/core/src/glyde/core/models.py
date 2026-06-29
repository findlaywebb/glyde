"""Domain models — the data shapes the rest of the system speaks.

Key types:
- ``Record`` — the example domain entity shipped with the template. It carries an
  id (minted by the api layer), a non-blank name, and a server-stamped canonical
  UTC ``created_at``. Replace it with the real domain model(s).

What this module does NOT do:
- No I/O, no clock reads, no id minting — the ``id`` and ``created_at`` are passed
  in by the api layer, which is the one clock/mint site.

Invariants:
- Models are frozen (``frozen=True``) and reject unknown fields (``extra='forbid'``):
  a domain value is immutable once built and never silently absorbs stray keys.
- ``created_at`` is a canonical ISO-8601 UTC string; sorting it lexicographically
  sorts chronologically.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class Record(BaseModel):
    """An example domain entity: an id, a non-blank name, and a creation instant.

    Construct from validated inputs; the id and ``created_at`` are supplied by the
    api layer (the clock/mint site), never generated here.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(description="Opaque unique id, minted by the api layer.")
    name: str = Field(min_length=1, description="Human-meaningful, non-blank name.")
    created_at: str = Field(description="Canonical ISO-8601 UTC creation timestamp.")
