"""Tests for the memorable two-word slug generator."""

import random
import re

from glyde.api.slug import new_slug

_SLUG = re.compile(r"^[a-z]+-[a-z]+$")


def test_new_slug_is_two_lowercase_words() -> None:
    """A fresh slug is two lowercase words joined by a hyphen."""
    assert _SLUG.fullmatch(new_slug(lambda _: False, rng=random.Random(0)))


def test_new_slug_retries_past_a_taken_candidate() -> None:
    """new_slug retries when a candidate is taken, returning a free pair."""
    seen: list[str] = []

    def is_taken(candidate: str) -> bool:
        seen.append(candidate)
        return len(seen) == 1  # the first candidate is taken, the rest are free

    slug = new_slug(is_taken, rng=random.Random(1))
    assert _SLUG.fullmatch(slug)
    assert len(seen) == 2


def test_new_slug_falls_back_to_a_numeric_suffix() -> None:
    """When every plain pair is taken, new_slug appends an incrementing numeric suffix."""
    slug = new_slug(lambda candidate: candidate.count("-") < 2, rng=random.Random(2), k=3)
    assert slug.endswith("-2")
    assert slug.count("-") == 2
