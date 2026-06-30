"""Pure derivation over the Digest IR — counts, integrity, reading estimate.

Glyde mints no id, clock, or random value in ``core``, but pure derivation from
already-built values is fine (``hashlib`` is stdlib). These helpers are computed
once at ingest by the api layer and stamped onto ``DigestMeta``.

Key callables:
- ``count_tokens`` — the number of ``word`` tokens across every prose segment.
- ``content_sha`` — the sha256 hex of the canonical source text (for dedup and
  integrity). For pre-segmented input with no source text, the caller passes the
  canonical segments JSON instead.
- ``estimate_reading_ms`` — the millisecond reading estimate at a given wpm.

Key constants:
- ``BASELINE_WPM`` — the words-per-minute the stored ``est_reading_ms`` is
  derived at (the reader re-derives live pacing from ``Preferences``).

What this module does NOT do:
- No clock, no id minting, no randomness, no I/O — every input arrives as an
  argument and every output is a pure function of it.
"""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING

from glyde.core.models import ProseSegment

if TYPE_CHECKING:
    from collections.abc import Iterable

    from glyde.core.models import Segment

BASELINE_WPM = 300


def count_tokens(segments: Iterable[Segment]) -> int:
    """Return the number of ``word`` tokens across every prose segment.

    Pauses and blocks contribute nothing; only ``ProseSegment`` tokens whose
    ``kind`` is ``word`` are counted (the unit ``est_reading_ms`` is derived on).

    Args:
        segments: The ordered reading-timeline segments.

    Returns:
        The total count of ``word`` tokens.
    """
    return sum(
        1
        for segment in segments
        if isinstance(segment, ProseSegment)
        for token in segment.tokens
        if token.kind == "word"
    )


def content_sha(source: str) -> str:
    """Return the sha256 hex digest of ``source`` (utf-8) for dedup + integrity.

    Args:
        source: The canonical source text, or — for pre-segmented input with no
            text — the canonical segments JSON.

    Returns:
        The 64-character lowercase hex sha256 digest.
    """
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


def estimate_reading_ms(token_count: int, wpm: int) -> int:
    """Return the reading-time estimate in milliseconds at ``wpm``.

    Args:
        token_count: The number of word tokens to read.
        wpm: The words-per-minute pace (e.g. ``BASELINE_WPM``).

    Returns:
        ``round(token_count / wpm * 60000)`` — milliseconds, rounded to int.
    """
    return round(token_count / wpm * 60000)
