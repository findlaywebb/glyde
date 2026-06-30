"""Wire projections of the Digest IR segment union — named, discriminated views.

Key types:
- ``TokenView`` — the wire projection of a streamed ``Token``.
- ``ProseSegmentView`` / ``PauseView`` / ``BlockView`` — the projected segment
  variants, each a NAMED ``ApiModel`` so the OpenAPI document emits a named
  ``components.schemas`` member the frontend aliases directly.
- ``SegmentView`` — the wire segment union: a Pydantic v2 discriminated union on
  ``type``, so a list of segments renders in OpenAPI as a ``oneOf`` of named
  ``$ref`` s carrying a ``type`` discriminator (never an anonymous ``anyOf``).

What this module does NOT do:
- No domain logic — pure schema projections of ``glyde.core`` segment models.

Invariants:
- Every field carries a ``description`` except the ``type`` discriminator (its
  ``Literal`` value is its own documentation). Defaults mirror the core models so
  a request body validates from partial JSON.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field

from glyde.api.schemas._base import ApiModel


class TokenView(ApiModel):
    """The wire projection of a streamed ``Token``."""

    text: str = Field(description="The token's text (one word or punctuation mark).")
    kind: Literal["word", "punct"] = Field(
        default="word", description="Token class: a word or a punctuation mark."
    )
    emphasis: Literal["none", "strong", "em", "code"] = Field(
        default="none", description="Agent-given emphasis for the token."
    )
    hold: float | None = Field(
        default=None, description="Optional coarse agent dwell hint (not milliseconds)."
    )


class ProseSegmentView(ApiModel):
    """The wire projection of a prose run."""

    type: Literal["prose"] = "prose"
    role: Literal["heading", "body", "list_item"] = Field(
        default="body", description="The run's structural role."
    )
    tokens: list[TokenView] = Field(description="The ordered prose tokens of the run.")


class PauseView(ApiModel):
    """The wire projection of a pause beat between runs."""

    type: Literal["pause"] = "pause"
    reason: Literal["clause", "sentence", "paragraph", "block_ahead"] = Field(
        description="Why the pause occurs; the reader maps it to a dwell."
    )
    duration_scale: float = Field(
        default=1.0, description="Coarse beat weight the reader scales the pause by."
    )


class BlockView(ApiModel):
    """The wire projection of a non-streamed block shown as a static card."""

    type: Literal["block"] = "block"
    kind: Literal["code", "table", "image", "quote", "math", "note"] = Field(
        description="The block kind, selecting which card the reader renders."
    )
    content: str = Field(description="The raw block content, shown verbatim, never streamed.")
    lang: str | None = Field(default=None, description="Code language for a code block, else null.")
    lead: str | None = Field(
        default=None, description="The prose runway sentence the block follows, else null."
    )
    alt: str | None = Field(
        default=None, description="Image alt text for an image block, else null."
    )
    linear_form: str | None = Field(
        default=None, description="Spoken form for promoted math, else null."
    )


SegmentView = Annotated[ProseSegmentView | PauseView | BlockView, Field(discriminator="type")]
