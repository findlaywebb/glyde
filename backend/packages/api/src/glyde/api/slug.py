"""Memorable two-word slug minting — the api layer's slug source.

Slugs are minted here (the api layer), beside ``ids.new_id``: the purity gate
forbids module-level ``random`` inward, so the ``random.Random`` draw is api-side.
A slug is the secondary UNIQUE key, 1:1 with the id; ``/d/{slug}`` resolves it.

Key callables:
- ``new_slug`` — draw a ``"{left}-{right}"`` pair from two packaged word pools,
  retrying on collision and falling back to a numeric suffix.

Invariants:
- The word pools are packaged assets (``importlib.resources``), loaded once.
- On ``is_taken`` collisions ``new_slug`` retries up to ``k`` fresh pairs, then
  appends an incrementing ``-N`` suffix until a free slug is found.
"""

from __future__ import annotations

import random
from functools import lru_cache
from importlib.resources import files
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

_FIRST_SUFFIX = 2


@lru_cache
def _pool(name: str) -> tuple[str, ...]:
    """Load and cache a packaged word pool (``left`` or ``right``)."""
    text = (files("glyde.api") / "wordbank" / f"{name}.txt").read_text(encoding="utf-8")
    return tuple(word for line in text.splitlines() if (word := line.strip()))


def new_slug(
    is_taken: Callable[[str], bool],
    *,
    rng: random.Random | None = None,
    k: int = 8,
) -> str:
    """Return a free ``"{left}-{right}"`` slug, retrying then suffixing on collision.

    Args:
        is_taken: Predicate returning True if a candidate slug already exists.
        rng: Optional seeded RNG (defaults to a fresh ``random.Random``).
        k: How many fresh pairs to try before falling back to a numeric suffix.

    Returns:
        A slug not rejected by ``is_taken``.
    """
    chooser = rng if rng is not None else random.Random()
    left, right = _pool("left"), _pool("right")
    candidate = ""
    for _ in range(k):
        candidate = f"{chooser.choice(left)}-{chooser.choice(right)}"
        if not is_taken(candidate):
            return candidate
    suffix = _FIRST_SUFFIX
    while is_taken(f"{candidate}-{suffix}"):
        suffix += 1
    return f"{candidate}-{suffix}"
