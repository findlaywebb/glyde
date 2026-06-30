"""Tests for ``compose_digest`` — the shared CLI/route composition."""

from collections.abc import Callable

from support.memory_store import InMemoryDigestStore

from glyde.api.compose import ComposeDeps, ComposeRequest, compose_digest
from glyde.core import Pause, ProseSegment, Segment, Token


def _deps(store: InMemoryDigestStore) -> ComposeDeps:
    """Build ComposeDeps with deterministic id/slug minters and frozen time."""
    ids = (f"id-{n}" for n in range(100))
    slugs = (f"slug-{n}" for n in range(100))
    return ComposeDeps(
        store=store,
        now="2025-01-01T00:00:00+00:00",
        new_id=lambda: next(ids),
        new_slug=lambda _is_taken: next(slugs),
        enricher=None,
    )


def test_compose_parses_text_and_derives_counts_then_persists() -> None:
    """compose_digest parses text to the IR, derives counts, and stores the digest."""
    store = InMemoryDigestStore()
    req = ComposeRequest(
        name="t", text="Run this.\n\n```py\nx=1\n```", segments=None, source_kind="cli"
    )
    digest = compose_digest(req, _deps(store))
    assert digest.meta.token_count == 2  # Run, this
    assert digest.meta.est_reading_ms == 400  # round(2 / 300 * 60000)
    assert any(segment.type == "block" for segment in digest.segments)
    assert store.get_by_slug(digest.meta.slug) == digest


def test_compose_uses_supplied_segments_when_no_text() -> None:
    """compose_digest uses pre-segmented input when text is absent."""
    store = InMemoryDigestStore()
    segments: list[Segment] = [
        ProseSegment(role="body", tokens=[Token(text="hi")]),
        Pause(reason="sentence"),
    ]
    req = ComposeRequest(name="s", text=None, segments=segments, source_kind="api")
    digest = compose_digest(req, _deps(store))
    assert digest.meta.token_count == 1
    assert [segment.type for segment in digest.segments] == ["prose", "pause"]


def test_compose_slug_closure_consults_the_store() -> None:
    """The slug minter receives an is_taken closure backed by the store."""
    store = InMemoryDigestStore()
    observed: list[bool] = []

    def slug_minter(is_taken: Callable[[str], bool]) -> str:
        observed.append(is_taken("brave-otter"))
        return "brave-otter"

    deps = ComposeDeps(
        store=store,
        now="2025-01-01T00:00:00+00:00",
        new_id=lambda: "id-1",
        new_slug=slug_minter,
        enricher=None,
    )
    compose_digest(ComposeRequest(name="t", text="hi", segments=None, source_kind="cli"), deps)
    assert observed == [False]  # the slug is free before this digest is stored
