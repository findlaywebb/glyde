"""The Glyde-Markdown parser: reading syntax to the Digest IR timeline.

Key callables:
- ``parse_glyde_markdown`` — parse Glyde-Markdown text into the ordered list of
  ``Segment`` s (prose runs, pauses, and blocks) the reader streams.

Syntax: ``#`` heading; ``-/*/+`` or ``N.`` list item; a blank line is a paragraph
pause; ```` ``` ```` fenced code; pipe table; ``![alt](src)`` image;
``:::pause … :::`` note; ``$$…$$`` math; ``> …`` quote. Inline ``==strong==``,
`` `code` ``, ``*em*`` / ``_em_``. A clause (``,;:``) or sentence (``.!?…``)
terminator splits prose into runs and sets the following pause's reason.

What this module does NOT do:
- No rendering, no pacing, no id/clock/slug minting — a pure, deterministic
  syntax-to-IR transform.

Invariants:
- Every block is preceded by a ``Pause(block_ahead)`` that supersedes any pending
  paragraph/sentence pause; a block's ``lead`` is the nearest preceding prose
  run's text, else ``None``. Consecutive list items are separated by
  ``Pause(clause)``. A blank line upgrades a pending sentence/clause pause to a
  paragraph pause (no stacked pauses). There is never a trailing pause at EOF.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Literal

from glyde.core.models import Pause, ProseSegment
from glyde.core.parsing.blocks import take_block
from glyde.core.parsing.prose import split_runs, tokenize_run

if TYPE_CHECKING:
    from glyde.core.models import Block, Segment, Token

__all__ = ["parse_glyde_markdown"]

_LIST_ITEM = re.compile(r"\s*(?:[-*+]|\d+\.)\s+(.*)")
_Reason = Literal["clause", "sentence", "paragraph", "block_ahead"]
_Role = Literal["heading", "body", "list_item"]


class _Timeline:
    """Accumulate segments with a pending-pause and last-prose-run discipline."""

    def __init__(self) -> None:
        """Start an empty timeline with no pending pause and no prior prose."""
        self.segments: list[Segment] = []
        self.last_prose: str | None = None
        self._pending: _Reason | None = None

    def _flush(self) -> None:
        """Emit and clear any pending pause before the next content segment."""
        if self._pending is not None:
            self.segments.append(Pause(reason=self._pending))
            self._pending = None

    def paragraph(self) -> None:
        """Set a paragraph pause as pending (a blank line; supersedes weaker)."""
        self._pending = "paragraph"

    def hold(self, reason: _Reason) -> None:
        """Set ``reason`` as the pending pause before the next content segment."""
        self._pending = reason

    def prose(self, role: _Role, tokens: list[Token]) -> None:
        """Flush any pending pause, append a prose run, and record it as the lead."""
        self._flush()
        self.segments.append(ProseSegment(role=role, tokens=tokens))
        self.last_prose = " ".join(token.text for token in tokens)

    def block(self, block: Block) -> None:
        """Emit a block-ahead pause (superseding pending) then the block."""
        self._pending = None
        self.segments.append(Pause(reason="block_ahead"))
        self.segments.append(block)
        self.last_prose = None


def parse_glyde_markdown(text: str) -> list[Segment]:
    """Parse Glyde-Markdown ``text`` into the ordered Digest IR segments.

    Args:
        text: The Glyde-Markdown source (newline-separated lines).

    Returns:
        The reading timeline: an ordered list of ``ProseSegment``, ``Pause``, and
        ``Block`` segments. Empty input yields an empty list.
    """
    lines = text.split("\n")
    timeline = _Timeline()
    index = 0
    while index < len(lines):
        line = lines[index]
        if line.strip() == "":
            timeline.paragraph()
            index += 1
            continue
        taken = take_block(lines, index, timeline.last_prose)
        if taken is not None:
            block, index = taken
            timeline.block(block)
            continue
        if line.startswith("#"):
            timeline.prose("heading", tokenize_run(line.lstrip("#").strip()))
            index += 1
            continue
        item = _LIST_ITEM.fullmatch(line)
        if item is not None:
            timeline.prose("list_item", tokenize_run(item.group(1)))
            timeline.hold("clause")
            index += 1
            continue
        for run_text, reason in split_runs(line):
            timeline.prose("body", tokenize_run(run_text))
            if reason is not None:
                timeline.hold(reason)
        index += 1
    return timeline.segments
