"""Hypothesis property tests for parser invariants vectors cannot exhaust.

These cover algorithmic invariants (no stacked pauses, no trailing pause, the
block-ahead cue, whitespace-free tokens, plain-prose round-trip) over many
generated inputs, complementing the pinned golden vectors.
"""

import itertools
import string

from hypothesis import given
from hypothesis import strategies as st

from glyde.core import Block, Pause, ProseSegment
from glyde.core.parsing import parse_glyde_markdown

# A small alphabet rich enough to exercise every branch (markers, terminators,
# structure chars) but free of control characters that muddy the invariants.
_ALPHABET = string.ascii_letters + string.digits + " \n.,;:!?-*+#|>=_`$()[]"
_TEXT = st.text(alphabet=_ALPHABET, max_size=80)
_WORDS = st.lists(
    st.text(alphabet=string.ascii_letters, min_size=1, max_size=6), min_size=1, max_size=8
)


@given(_TEXT)
def test_no_two_consecutive_pauses(text: str) -> None:
    """Pauses are always separated by a content segment (no stacked pauses)."""
    segments = parse_glyde_markdown(text)
    pairs = itertools.pairwise(segments)
    assert not any(isinstance(a, Pause) and isinstance(b, Pause) for a, b in pairs)


@given(_TEXT)
def test_never_a_trailing_pause(text: str) -> None:
    """The final segment is never a pause (no trailing pause at end of input)."""
    segments = parse_glyde_markdown(text)
    assert not segments or not isinstance(segments[-1], Pause)


@given(_TEXT)
def test_every_block_follows_a_block_ahead_pause(text: str) -> None:
    """Every block is immediately preceded by a Pause(block_ahead) cue."""
    segments = parse_glyde_markdown(text)
    for position, segment in enumerate(segments):
        if isinstance(segment, Block):
            assert position > 0
            previous = segments[position - 1]
            assert isinstance(previous, Pause)
            assert previous.reason == "block_ahead"


@given(_TEXT)
def test_prose_tokens_are_non_empty_and_whitespace_free(text: str) -> None:
    """Every prose token carries non-empty, whitespace-free text."""
    for segment in parse_glyde_markdown(text):
        if isinstance(segment, ProseSegment):
            for token in segment.tokens:
                assert token.text
                assert not any(char.isspace() for char in token.text)


@given(_WORDS)
def test_plain_words_round_trip_to_one_body_run(words: list[str]) -> None:
    """Plain space-joined words parse to a single body run of those words."""
    segments = parse_glyde_markdown(" ".join(words))
    assert len(segments) == 1
    only = segments[0]
    assert isinstance(only, ProseSegment)
    assert only.role == "body"
    assert [token.text for token in only.tokens] == words


@given(
    st.text(alphabet=string.ascii_letters, min_size=1, max_size=10),
    st.sampled_from(list(",;:.!?")),
)
def test_trailing_terminator_retained_in_last_token(word: str, terminator: str) -> None:
    """A word followed by a trailing terminator retains it in the last token's text."""
    segments = parse_glyde_markdown(word + terminator)
    prose_segments = [s for s in segments if isinstance(s, ProseSegment)]
    assert prose_segments, "at least one prose segment expected"
    last_prose = prose_segments[-1]
    assert last_prose.tokens[-1].text == word + terminator
