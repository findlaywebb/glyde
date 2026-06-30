"""Prose tokenization and run splitting for the Glyde-Markdown parser.

Key callables:
- ``split_runs`` — split one prose line into ``(run_text, pause_reason)`` pairs
  at clause (``,;:``) and sentence (``.!?…``) terminators.
- ``tokenize_run`` — turn a run's text into ``Token`` s, detecting inline
  emphasis spans (``==strong==``, `` `code` ``, ``*em*`` / ``_em_``).

What this module does NOT do:
- No block detection (that is ``blocks``), no timeline assembly (that is the
  package orchestrator). Pure and deterministic.

Invariants:
- Emphasis does not nest; an unmatched or inner delimiter is literal text.
- A trailing terminator is retained in the run's last word token (e.g.
  ``"world."`` or ``"done,"``), so the visible character stays on the rendered
  word. It still sets the FOLLOWING pause's reason. A terminator not followed
  by whitespace or the line end (e.g. the dot in ``3.14``) is ordinary text,
  not a split point.
- When a terminator immediately follows an emphasis span (e.g. ``==done==.``),
  ``tokenize_run`` merges it onto the preceding word token so no bare
  single-punctuation token is emitted.
- Tokens are whitespace-free and non-empty (the text is split on whitespace).
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Literal, cast

from glyde.core.models import Token

if TYPE_CHECKING:
    from collections.abc import Iterator

_CLAUSE = ",;:"
_SENTENCE = ".!?…"
_TERMINATORS: frozenset[str] = frozenset(_CLAUSE + _SENTENCE)
_SPAN = re.compile(r"==(.+?)==|`(.+?)`|\*(.+?)\*|_(.+?)_")
_EMPHASIS: dict[int, Literal["strong", "code", "em"]] = {1: "strong", 2: "code", 3: "em", 4: "em"}


def _reason(char: str) -> Literal["clause", "sentence"] | None:
    """Classify a terminator char as a clause/sentence reason, or ``None``."""
    if char in _CLAUSE:
        return "clause"
    if char in _SENTENCE:
        return "sentence"
    return None


def split_runs(line: str) -> list[tuple[str, Literal["clause", "sentence"] | None]]:
    """Split a prose line into ``(run_text, reason)`` pairs at terminators.

    A run ends at a clause/sentence terminator followed by whitespace or the line
    end; the terminator sets that run's trailing pause ``reason``. The final run
    carries ``None`` when the line ends without a terminator. Empty runs (e.g. a
    leading terminator) are dropped.

    Args:
        line: One non-blank prose line (no trailing newline).

    Returns:
        The ordered ``(run_text, reason)`` pairs, ``run_text`` stripped.
    """
    runs: list[tuple[str, Literal["clause", "sentence"] | None]] = []
    buffer: list[str] = []
    index = 0
    length = len(line)
    while index < length:
        char = line[index]
        reason = _reason(char)
        if reason is not None and (index + 1 >= length or line[index + 1].isspace()):
            if buffer:  # only retain when there is a word to attach it to
                buffer.append(char)
            text = "".join(buffer).strip()
            if text:
                runs.append((text, reason))
            buffer = []
            index += 1
            while index < length and line[index].isspace():
                index += 1
            continue
        buffer.append(char)
        index += 1
    tail = "".join(buffer).strip()
    if tail:
        runs.append((tail, None))
    return runs


def _words(text: str, emphasis: Literal["none", "strong", "em", "code"]) -> Iterator[Token]:
    """Yield a ``Token`` for each whitespace-split word in ``text``."""
    for word in text.split():
        yield Token(text=word, emphasis=emphasis)


def tokenize_run(text: str) -> list[Token]:
    """Tokenize a run's text into ``Token`` s, applying inline emphasis spans.

    Text outside any emphasis span tokenizes to plain ``word`` tokens; the text
    captured inside ``==…==`` / `` `…` `` / ``*…*`` / ``_…_`` takes that span's
    emphasis. Spans do not nest; an unmatched delimiter is literal text.

    When a terminator immediately follows a span with no intervening whitespace
    (e.g. ``==done==.``), the terminator is merged onto the span's last token so
    no bare single-punctuation token is emitted.

    Args:
        text: One run's text (may carry a trailing retained terminator).

    Returns:
        The ordered tokens for the run.
    """
    tokens: list[Token] = []
    position = 0
    for match in _SPAN.finditer(text):
        tokens.extend(_words(text[position : match.start()], "none"))
        group = cast("int", match.lastindex)
        tokens.extend(_words(match.group(group), _EMPHASIS[group]))
        position = match.end()
    tokens.extend(_words(text[position:], "none"))
    # Merge a trailing bare terminator onto the preceding token so an emphasis
    # span like ==done==. never emits a standalone punctuation token.
    if len(tokens) >= 2 and tokens[-1].text in _TERMINATORS:
        tail = tokens.pop()
        prev = tokens[-1]
        tokens[-1] = Token(text=prev.text + tail.text, emphasis=prev.emphasis)
    return tokens
