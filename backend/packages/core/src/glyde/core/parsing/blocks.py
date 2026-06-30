"""Block detection for the Glyde-Markdown parser.

Key callables:
- ``take_block`` — try to parse a block starting at a line; return
  ``(Block, next_index)`` or ``None`` when the line opens no block. The block
  kinds: fenced code, pipe table, image, ``$$`` math, ``:::`` note, ``>`` quote.

What this module does NOT do:
- No prose tokenisation (``prose``); no block-ahead cue or ``lead`` derivation
  (the package orchestrator owns the timeline and passes ``lead`` in). Pure.

Invariants:
- Each detector consumes whole lines and returns the index of the first line it
  did NOT consume, so the orchestrator resumes cleanly after a multi-line block.
  An unterminated fence/note runs to end of input.
"""

from __future__ import annotations

import re

from glyde.core.models import Block

_FENCE = "```"
_NOTE = ":::"
_MATH = "$$"
_IMAGE = re.compile(r"!\[(.*?)\]\((.*?)\)")

type _Taken = tuple[Block, int] | None


def _take_fence(lines: list[str], start: int, lead: str | None) -> _Taken:
    """Parse a ```` ``` ````-fenced code block (optionally lang-tagged)."""
    if not lines[start].startswith(_FENCE):
        return None
    lang = lines[start][len(_FENCE) :].strip() or None
    body, index = _collect_until(lines, start + 1, _FENCE)
    return Block(kind="code", content="\n".join(body), lang=lang, lead=lead), index


def _take_table(lines: list[str], start: int, lead: str | None) -> _Taken:
    """Parse a run of consecutive pipe-table lines into one table block."""
    if not lines[start].startswith("|"):
        return None
    rows: list[str] = []
    index = start
    while index < len(lines) and lines[index].startswith("|"):
        rows.append(lines[index])
        index += 1
    return Block(kind="table", content="\n".join(rows), lead=lead), index


def _take_image(lines: list[str], start: int, lead: str | None) -> _Taken:
    """Parse a whole-line ``![alt](src)`` image into an image block."""
    match = _IMAGE.fullmatch(lines[start].strip())
    if match is None:
        return None
    return Block(kind="image", content=match.group(2), alt=match.group(1), lead=lead), start + 1


def _take_math(lines: list[str], start: int, lead: str | None) -> _Taken:
    """Parse a single-line ``$$…$$`` into a math block."""
    line = lines[start].strip()
    if not (line.startswith(_MATH) and line.endswith(_MATH) and len(line) > 2 * len(_MATH)):
        return None
    return Block(kind="math", content=line[len(_MATH) : -len(_MATH)].strip(), lead=lead), start + 1


def _take_note(lines: list[str], start: int, lead: str | None) -> _Taken:
    """Parse a ``:::…`` … ``:::`` fenced note into a note block."""
    if not lines[start].strip().startswith(_NOTE):
        return None
    body, index = _collect_until(lines, start + 1, _NOTE)
    return Block(kind="note", content="\n".join(body).strip(), lead=lead), index


def _take_quote(lines: list[str], start: int, lead: str | None) -> _Taken:
    """Parse a run of consecutive ``>`` lines into one quote block."""
    if not lines[start].startswith(">"):
        return None
    rows: list[str] = []
    index = start
    while index < len(lines) and lines[index].startswith(">"):
        rows.append(lines[index][1:].strip())
        index += 1
    return Block(kind="quote", content="\n".join(rows), lead=lead), index


def _collect_until(lines: list[str], start: int, closer: str) -> tuple[list[str], int]:
    """Collect lines from ``start`` up to a ``closer`` line; return body + next index.

    The next index is past the closer when one is found, else end of input (an
    unterminated fence/note runs to the end).
    """
    body: list[str] = []
    index = start
    while index < len(lines) and lines[index].strip() != closer:
        body.append(lines[index])
        index += 1
    return body, index + 1 if index < len(lines) else index


_DETECTORS = (_take_fence, _take_table, _take_image, _take_math, _take_note, _take_quote)


def take_block(lines: list[str], start: int, lead: str | None) -> _Taken:
    """Return ``(Block, next_index)`` for the block at ``start``, or ``None``.

    Args:
        lines: The full list of input lines.
        start: The index of the candidate opening line.
        lead: The nearest preceding prose run's text (the block's runway), or
            ``None`` when no prose precedes it.

    Returns:
        The parsed block and the index to resume from, or ``None`` when the line
        opens no block.
    """
    for detector in _DETECTORS:
        taken = detector(lines, start, lead)
        if taken is not None:
            return taken
    return None
