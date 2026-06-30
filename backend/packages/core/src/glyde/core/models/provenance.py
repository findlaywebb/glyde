"""Provenance — what produced a digest, and how it reached Glyde.

Key types:
- ``Provenance`` — a 1:1, immutable, single-hop record of a digest's origin:
  the kind of source, an optional origin locator, the producing agent/model,
  the ingestion channel, and whether an enrich pass touched it.

What this module does NOT do:
- No multi-hop lineage and no audit trail: provenance is a single hop captured
  at ingest, not an event log.

Invariants:
- Frozen, ``extra='forbid'``. ``source_kind`` and ``ingested_via`` are closed
  ``Literal`` sets; ``origin`` and ``producer`` are free-form and optional.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict


class Provenance(BaseModel):
    """Where a digest came from and how it was ingested (single hop)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    source_kind: Literal["agent", "file", "cli", "paste", "pipe", "api"]
    origin: str | None = None
    producer: str | None = None
    ingested_via: Literal["cli", "api", "mcp"] = "cli"
    enriched: bool = False
