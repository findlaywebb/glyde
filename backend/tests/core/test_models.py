"""Tests for the Digest IR models."""

import pytest
from pydantic import TypeAdapter, ValidationError
from support import factories

from glyde.core import (
    Block,
    Digest,
    Pause,
    Preferences,
    ProseSegment,
    Provenance,
    Segment,
    Token,
)


def test_token_defaults_to_a_plain_word() -> None:
    """A Token defaults to a word with no emphasis and no dwell hint."""
    tok = Token(text="hello")
    assert (tok.kind, tok.emphasis, tok.hold) == ("word", "none", None)


def test_ir_models_are_frozen() -> None:
    """IR models are immutable once built."""
    tok = Token(text="x")
    with pytest.raises(ValidationError):
        tok.text = "y"


def test_ir_models_reject_unknown_fields() -> None:
    """extra=forbid rejects stray keys rather than silently dropping them."""
    with pytest.raises(ValidationError):
        Token.model_validate({"text": "x", "weight": 3})


def test_segment_union_discriminates_on_type() -> None:
    """The Segment union routes each payload to its variant by the `type` tag."""
    adapter = TypeAdapter(Segment)
    assert isinstance(
        adapter.validate_python({"type": "prose", "tokens": [{"text": "x"}]}), ProseSegment
    )
    assert isinstance(adapter.validate_python({"type": "pause", "reason": "clause"}), Pause)
    assert isinstance(
        adapter.validate_python({"type": "block", "kind": "code", "content": "x=1"}), Block
    )


def test_digest_round_trips_through_json_preserving_segment_types() -> None:
    """A Digest with mixed segments round-trips, keeping each segment's type."""
    dig = factories.digest(
        segments=[factories.prose("a"), factories.pause("clause"), factories.block("code")]
    )
    restored = Digest.model_validate_json(dig.model_dump_json())
    assert [segment.type for segment in restored.segments] == ["prose", "pause", "block"]
    assert restored == dig


def test_digest_meta_rejects_blank_name() -> None:
    """DigestMeta enforces a non-blank name."""
    with pytest.raises(ValidationError):
        factories.digest(name="")


def test_preferences_default_to_guided_at_baseline_speed() -> None:
    """Preferences default to the guided mode at the baseline 300 wpm."""
    prefs = Preferences()
    assert (prefs.mode, prefs.wpm) == ("guided", 300)


def test_provenance_defaults_to_cli_unenriched() -> None:
    """Provenance defaults ingested_via to cli and enriched to False."""
    prov = Provenance(source_kind="cli")
    assert (prov.ingested_via, prov.enriched) == ("cli", False)
