"""Per-user reading preferences — keyed by ``owner_id``, never on a digest.

Key types:
- ``Preferences`` — the per-user reading configuration: the default reading
  mode, speed, context treatment, and the comfort settings (font, size,
  spacing, theme). Every field has a default, so a partial update validates and
  missing fields fall to the default.

What this module does NOT do:
- No digest content: preferences are per-user settings, never stored on a
  ``Digest``. No pacing maths: the reader derives dwell/pivot from these values
  plus the cadence constants.

Invariants:
- Frozen, ``extra='forbid'``. The default ``mode`` is ``guided``; the reader
  persists the user's last-used mode back here so it is restored next open.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict


class Preferences(BaseModel):
    """A user's reading configuration; every field carries a default."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    owner_id: str = "local"
    mode: Literal["rsvp", "guided", "fading"] = "guided"
    wpm: int = 300
    context: Literal["off", "ab", "line", "sentence"] = "ab"
    ctx_scale: float = 0.7
    chunk: int = 1
    size_px: int = 64
    letter_spacing_em: float = 0.04
    font: Literal["atkinson", "lexend", "opendyslexic", "system", "serif", "mono"] = "atkinson"
    theme: Literal["dark", "light", "sepia"] = "dark"
    ramp: bool = True
