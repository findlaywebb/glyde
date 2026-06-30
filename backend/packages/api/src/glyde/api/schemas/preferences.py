"""Wire projection for the preferences surface — a projection of ``Preferences``.

Key types:
- ``PreferencesView`` — the per-user reading config on the wire. Every field
  carries a default mirroring the core ``Preferences``, so a partial ``PUT`` body
  validates under ``extra='forbid'`` (which rejects unknown keys, never missing
  ones — missing fields fall to their defaults) and the response is the full
  object.

What this module does NOT do:
- No pacing maths and no storage — pure schema. ``PUT`` is full-replace, so the
  client always sends the complete object.
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from glyde.api.schemas._base import ApiModel


class PreferencesView(ApiModel):
    """The wire projection of a user's reading preferences (every field defaulted)."""

    owner_id: str = Field(default="local", description="The owning user (single-user in v1).")
    mode: Literal["rsvp", "guided", "fading", "focus"] = Field(
        default="guided", description="The reading mode; default guided, last-used persisted."
    )
    wpm: int = Field(default=300, description="Reading speed in words per minute.")
    context: Literal["off", "ab", "line", "sentence"] = Field(
        default="ab", description="The RSVP context-window treatment."
    )
    ctx_scale: float = Field(default=0.7, description="Relative size of dimmed context words.")
    chunk: int = Field(default=1, description="Words shown per flash.")
    size_px: int = Field(default=64, description="Reading word size in pixels.")
    letter_spacing_em: float = Field(default=0.04, description="Letter spacing in em.")
    font: Literal["atkinson", "lexend", "opendyslexic", "system", "serif", "mono"] = Field(
        default="atkinson", description="The reading typeface."
    )
    theme: Literal["dark", "light", "sepia"] = Field(
        default="dark", description="The colour theme."
    )
    ramp: bool = Field(default=True, description="Ease into the target speed over the first words.")
