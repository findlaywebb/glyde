"""Tests for the pure derivation helpers over the Digest IR."""

from glyde.core import Block, Pause, ProseSegment, Token
from glyde.core.derive import BASELINE_WPM, content_sha, count_tokens, estimate_reading_ms


def test_count_tokens_counts_only_word_tokens_in_prose() -> None:
    """count_tokens sums word tokens across prose, ignoring punct, pauses, blocks."""
    segments = [
        ProseSegment(
            role="body",
            tokens=[Token(text="a"), Token(text=".", kind="punct"), Token(text="b")],
        ),
        Pause(reason="sentence"),
        Block(kind="code", content="x=1"),
    ]
    assert count_tokens(segments) == 2


def test_count_tokens_of_no_segments_is_zero() -> None:
    """count_tokens of an empty timeline is zero."""
    assert count_tokens([]) == 0


def test_content_sha_is_the_pinned_sha256_hex() -> None:
    """content_sha is the sha256 hex of the utf-8 source (pinned golden)."""
    assert content_sha("hello") == (
        "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
    )


def test_content_sha_differs_by_input() -> None:
    """Different sources hash to different digests."""
    assert content_sha("a") != content_sha("b")


def test_estimate_reading_ms_at_baseline_is_one_minute_for_300_words() -> None:
    """At the baseline 300 wpm, 300 words estimate to 60000 ms."""
    assert estimate_reading_ms(300, BASELINE_WPM) == 60000


def test_estimate_reading_ms_rounds_to_the_nearest_millisecond() -> None:
    """Two words at 300 wpm round to 400 ms (pinned golden)."""
    assert estimate_reading_ms(2, 300) == 400
