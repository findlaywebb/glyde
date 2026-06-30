"""The template ``Record`` model — transitional, removed when the IR lands fully.

Key types:
- ``Record`` — the example domain entity shipped with the template (an
  api-minted id, a non-blank name, a server-stamped canonical UTC timestamp).

This model is retained only while the example records vertical coexists with the
Digest IR during the foundation build; it carries no new behaviour and is
deleted once the IR replaces it end to end.

Invariants:
- Frozen, ``extra='forbid'``. ``id`` and ``created_at`` are supplied by the api
  layer (the clock/mint site), never generated here.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class Record(BaseModel):
    """An example domain entity: an id, a non-blank name, and a creation instant."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(description="Opaque unique id, minted by the api layer.")
    name: str = Field(min_length=1, description="Human-meaningful, non-blank name.")
    created_at: str = Field(description="Canonical ISO-8601 UTC creation timestamp.")
