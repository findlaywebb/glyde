"""Wire projections for the digests surface — projections of ``Digest``.

Key types:
- ``ProvenanceView`` / ``ReadingHintView`` / ``DigestMetaView`` — the projected
  digest metadata.
- ``DigestView`` — the full read projection (``meta`` + the discriminated
  ``segments`` list).
- ``CountsView`` / ``DigestListItemView`` — the list projection (``meta`` plus
  derived ``counts``).
- ``CreateDigestRequest`` — the create body; exactly one of ``text`` /
  ``segments`` is supplied, and the server mints id/slug and stamps time.

What this module does NOT do:
- No clock, storage, or id/slug minting — pure schema definitions.

Invariants:
- Every field carries a ``description``. ``DigestView`` projects a core ``Digest``
  via ``model_validate`` (``from_attributes``); the discriminated ``SegmentView``
  routes each core segment by its ``type``.
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from glyde.api.schemas._base import ApiModel
from glyde.api.schemas.segments import (
    SegmentView,  # noqa: TC001 - runtime-needed: pydantic resolves the list[SegmentView] field
)


class ProvenanceView(ApiModel):
    """The wire projection of a digest's provenance."""

    source_kind: Literal["agent", "file", "cli", "paste", "pipe", "api"] = Field(
        description="The kind of source the digest came from."
    )
    origin: str | None = Field(
        default=None, description="Origin locator (path, url, repo@sha, run-id), else null."
    )
    producer: str | None = Field(
        default=None, description="The producing agent/model label, else null."
    )
    ingested_via: Literal["cli", "api", "mcp"] = Field(
        default="cli", description="The channel the digest was ingested through."
    )
    enriched: bool = Field(
        default=False, description="Whether an enrich pass structured the source."
    )


class ReadingHintView(ApiModel):
    """The wire projection of an optional per-digest reading-mode hint."""

    suggested_mode: Literal["rsvp", "guided", "fading"] = Field(
        description="The reading mode this digest suggests."
    )


class DigestMetaView(ApiModel):
    """The wire projection of a digest's relation-stable metadata."""

    id: str = Field(description="Opaque api-minted id; the relation-stable key.")
    slug: str = Field(description="Memorable two-word slug; unique, 1:1 with the id.")
    name: str = Field(description="The agent-given semantic title.")
    provenance: ProvenanceView = Field(description="Where the digest came from and how.")
    created_at: str = Field(description="Canonical ISO-8601 UTC creation timestamp.")
    token_count: int = Field(description="Number of word tokens, derived at ingest.")
    est_reading_ms: int = Field(description="Reading-time estimate in ms at the baseline wpm.")
    content_sha: str = Field(description="sha256 of the source, for dedup and integrity.")
    ir_version: int = Field(description="The IR schema version the digest was built under.")
    owner_id: str = Field(description="The owning user (single-user 'local' in v1).")
    tags: list[str] = Field(description="Free-form tags for the digest.")
    reading_hint: ReadingHintView | None = Field(
        default=None, description="An optional suggested reading mode, else null."
    )


class DigestView(ApiModel):
    """The full read projection of a digest: metadata plus the segment timeline."""

    meta: DigestMetaView = Field(description="The digest's relation-stable metadata.")
    segments: list[SegmentView] = Field(
        description="The ordered reading-timeline segments (prose, pauses, blocks)."
    )


class CountsView(ApiModel):
    """The derived shape counts shown on a library list item."""

    words: int = Field(description="Total word tokens across the digest's prose.")
    blocks_by_kind: dict[str, int] = Field(description="Count of blocks keyed by block kind.")


class DigestListItemView(ApiModel):
    """A library list item: digest metadata plus its derived counts."""

    meta: DigestMetaView = Field(description="The digest's relation-stable metadata.")
    counts: CountsView = Field(description="Derived word and block-kind counts.")


class CreateDigestRequest(ApiModel):
    """The create body; exactly one of ``text`` / ``segments`` is required."""

    name: str = Field(min_length=1, description="The agent-given semantic title (non-blank).")
    text: str | None = Field(
        default=None, description="Glyde-Markdown source to parse, if not pre-segmented."
    )
    segments: list[SegmentView] | None = Field(
        default=None, description="Pre-segmented IR, if not supplying text."
    )
    source_kind: Literal["agent", "file", "cli", "paste", "pipe", "api"] = Field(
        description="The kind of source the digest came from."
    )
    origin: str | None = Field(default=None, description="Origin locator, else null.")
    producer: str | None = Field(default=None, description="The producing agent/model label.")
    ingested_via: Literal["cli", "api", "mcp"] = Field(
        default="cli", description="The channel the digest was ingested through."
    )
    tags: list[str] = Field(default_factory=list, description="Free-form tags for the digest.")
    enrich: bool = Field(
        default=False, description="Request an enrich pass on raw text when available."
    )

    @model_validator(mode="after")
    def _exactly_one_source(self) -> CreateDigestRequest:
        """Require exactly one of ``text`` / ``segments`` (neither/both is a 422)."""
        if (self.text is None) == (self.segments is None):
            msg = "provide exactly one of 'text' or 'segments'"
            raise ValueError(msg)
        return self
