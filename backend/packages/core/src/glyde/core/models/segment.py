"""The ordered reading-timeline elements: a discriminated union on ``type``.

Key types:
- ``ProseSegment`` — a run of streamed prose ``Token`` s with a structural role.
- ``Pause`` — a felt beat between runs, carrying its ``reason`` and a coarse
  ``duration_scale`` weight (never milliseconds).
- ``Block`` — non-streamed content (code, table, image, quote, math, note)
  shown as a static card; its ``content`` is shown verbatim, never flashed
  word-by-word.
- ``Segment`` — the timeline element: ``Annotated[..., discriminator="type"]``,
  so the api projection serialises as a ``oneOf`` with a ``type`` discriminator
  rather than an anonymous ``anyOf``.

What this module does NOT do:
- No rendering and no pacing maths. A ``Pause`` carries the ``reason`` and a
  coarse weight; the reader maps those to a dwell. A ``Block`` carries the raw
  body; the reader renders the card.

Invariants:
- Frozen, ``extra='forbid'``. Each variant's ``type`` is a distinct ``Literal``
  — the discriminant the union is keyed on.
- ``Block.content`` is raw block body, never tokenised; ``lead`` is the prose
  runway sentence the block follows, or ``None`` when no prose precedes it.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from glyde.core.models.token import (
    Token,  # noqa: TC001 - runtime-needed: pydantic resolves the list[Token] field type
)


class ProseSegment(BaseModel):
    """A run of prose tokens with a structural role (heading/body/list_item)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    type: Literal["prose"] = "prose"
    role: Literal["heading", "body", "list_item"] = "body"
    tokens: list[Token]


class Pause(BaseModel):
    """A felt beat between runs; the reader maps reason + scale to a dwell."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    type: Literal["pause"] = "pause"
    reason: Literal["clause", "sentence", "paragraph", "block_ahead"]
    duration_scale: float = 1.0


class Block(BaseModel):
    """Non-streamed content shown as a static card, discriminated by ``kind``."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    type: Literal["block"] = "block"
    kind: Literal["code", "table", "image", "quote", "math", "note"]
    content: str
    lang: str | None = None
    lead: str | None = None
    alt: str | None = None
    linear_form: str | None = None


Segment = Annotated[ProseSegment | Pause | Block, Field(discriminator="type")]
