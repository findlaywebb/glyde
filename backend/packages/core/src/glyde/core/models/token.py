"""The streaming atom: a single token on the reading reticle.

Key types:
- ``Token`` — one word (or punctuation mark) the reader flashes, carrying its
  agent-given emphasis and an optional coarse dwell hint.

What this module does NOT do:
- No pacing maths. ``hold`` is a coarse agent hint, never a millisecond dwell:
  the reader computes the real dwell from ``Preferences`` and the cadence
  constants, never from this field.

Invariants:
- Frozen and ``extra='forbid'``: a token is immutable once built and never
  absorbs stray keys.
- ``kind`` is ``word`` or ``punct`` only. No frequency class (``number`` /
  ``low_freq``) exists yet — there is no lexicon — so the current parser emits
  only ``word`` tokens.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict


class Token(BaseModel):
    """A single streamed token: its text, class, emphasis, and a dwell hint."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    text: str
    kind: Literal["word", "punct"] = "word"
    emphasis: Literal["none", "strong", "em", "code"] = "none"
    hold: float | None = None
