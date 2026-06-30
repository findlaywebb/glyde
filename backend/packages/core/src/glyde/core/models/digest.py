"""The digest aggregate: a named, traceable reading timeline with its metadata.

Key types:
- ``ReadingHint`` — an optional per-digest suggestion of a reading mode (never
  a user preference, which lives on ``Preferences``).
- ``DigestMeta`` — the relation-stable metadata: the api-minted ``id``, the
  memorable ``slug``, the agent-given ``name``, ``provenance``, the
  server-stamped ``created_at``, and the values derived once at ingest
  (``token_count``, ``est_reading_ms``, ``content_sha``).
- ``Digest`` — the aggregate: ``meta`` plus the ordered ``segments`` timeline.

What this module does NOT do:
- No id minting, no clock reads, no derivation: ``id``/``created_at`` arrive
  from the api layer and the derived counts are computed by ``glyde.core.derive``
  and passed in. Reading settings are NEVER stored here — they are per-user
  ``Preferences``; a digest carries at most the optional ``reading_hint``.

Invariants:
- Frozen, ``extra='forbid'``. ``slug`` is unique and 1:1 with ``id``;
  ``created_at`` is a canonical ISO-8601 UTC string (sorts chronologically).
- ``est_reading_ms`` is millisecond-native (derived at ``BASELINE_WPM``); the
  library formats it for display.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from glyde.core.models.provenance import (
    Provenance,  # noqa: TC001 - runtime-needed: pydantic resolves the provenance field type
)
from glyde.core.models.segment import (
    Segment,  # noqa: TC001 - runtime-needed: pydantic resolves the list[Segment] field type
)


class ReadingHint(BaseModel):
    """An optional per-digest suggestion of which reading mode suits it."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    suggested_mode: Literal["rsvp", "guided", "fading", "focus"]


class DigestMeta(BaseModel):
    """Relation-stable digest metadata: identity, provenance, derived counts."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    slug: str
    name: str = Field(min_length=1)
    provenance: Provenance
    created_at: str
    token_count: int
    est_reading_ms: int
    content_sha: str
    ir_version: int = 1
    owner_id: str = "local"
    tags: list[str] = Field(default_factory=list)
    reading_hint: ReadingHint | None = None


class Digest(BaseModel):
    """A digest: its metadata plus the ordered reading-timeline segments."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    meta: DigestMeta
    segments: list[Segment]
