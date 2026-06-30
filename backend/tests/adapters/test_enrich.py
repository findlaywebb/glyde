"""Tests for the HAIKU enrich path: adapter, provider, and compose_digest gate logic.

Covers:
- ``glyde.adapters.enrich.enrich`` — the Anthropic adapter (via a hand-written
  fake client; no real API call), including the bad-output guards (truncation,
  empty content, non-text block, empty text).
- ``glyde.api.enrich.get_enricher`` — key-presence gate (None vs callable),
  treating a blank key as absent.
- ``compose_digest`` enrich gate — enriches only when enrich=True AND an enricher
  is present AND the text has no detected structure; falls back gracefully on any
  failure.

No ``unittest.mock`` or ``pytest_mock`` is used. The Anthropic client is replaced
by a hand-written fake that constructs real ``anthropic.types`` objects so the
``isinstance`` checks inside the adapter run against genuine response shapes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import anthropic.types
import pytest
from support.memory_store import InMemoryDigestStore

from glyde.adapters.enrich import enrich
from glyde.api.compose import ComposeDeps, ComposeRequest, compose_digest
from glyde.api.enrich import get_enricher
from glyde.api.settings import Settings

if TYPE_CHECKING:
    from collections.abc import Callable

# ---------------------------------------------------------------------------
# Hand-written fake Anthropic client (real anthropic.types objects)
# ---------------------------------------------------------------------------


def _message(
    *,
    text: str | None = None,
    content: list[anthropic.types.ContentBlock] | None = None,
    stop_reason: str = "end_turn",
) -> anthropic.types.Message:
    """Build a real ``anthropic.types.Message`` for the fake client to return.

    Pass ``text`` for the common single-TextBlock case, or ``content`` to supply
    an explicit block list (empty, or a non-text block) for the guard tests.
    """
    blocks = (
        content
        if content is not None
        else [anthropic.types.TextBlock(type="text", text=text or "")]
    )
    return anthropic.types.Message(
        id="fake-msg-id",
        content=blocks,
        model="claude-haiku-4-5",
        role="assistant",
        type="message",
        stop_reason=stop_reason,  # ty: ignore[invalid-argument-type]
        usage=anthropic.types.Usage(input_tokens=1, output_tokens=1),
    )


class _FakeMessages:
    """Fake Anthropic messages resource returning a pre-built canned message."""

    def __init__(self, message: anthropic.types.Message) -> None:
        """Store the ``Message`` that ``create`` will return."""
        self._message = message

    def create(self, **_kwargs: object) -> anthropic.types.Message:
        """Return the canned ``Message`` regardless of the request arguments."""
        return self._message


class _FakeClient:
    """Fake Anthropic client exposing only the ``messages.create`` surface."""

    def __init__(self, message: anthropic.types.Message) -> None:
        """Wrap ``message`` in a fake messages resource."""
        self.messages = _FakeMessages(message)


def _client(**kwargs: object) -> _FakeClient:
    """Build a fake client whose ``messages.create`` returns ``_message(**kwargs)``."""
    return _FakeClient(_message(**kwargs))  # ty: ignore[invalid-argument-type]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _deps(
    store: InMemoryDigestStore, *, enricher: Callable[[str], str] | None = None
) -> ComposeDeps:
    """Build ``ComposeDeps`` with deterministic minters and optional enricher."""
    ids = (f"id-{n}" for n in range(100))
    slugs = (f"slug-{n}" for n in range(100))
    return ComposeDeps(
        store=store,
        now="2025-01-01T00:00:00+00:00",
        new_id=lambda: next(ids),
        new_slug=lambda _is_taken: next(slugs),
        enricher=enricher,
    )


# ---------------------------------------------------------------------------
# Adapter tests (glyde.adapters.enrich.enrich)
# ---------------------------------------------------------------------------


class TestEnrichAdapter:
    """The adapter returns good text and rejects every bad-output shape."""

    def test_returns_text_from_canned_response(self) -> None:
        """enrich() extracts and returns the TextBlock text from the fake client."""
        fake = _client(text="## Structured\nbody text")
        result = enrich("raw input", api_key="dummy", client=fake)  # ty: ignore[invalid-argument-type]
        assert result == "## Structured\nbody text"

    def test_raises_on_truncated_response(self) -> None:
        """enrich() raises when the response was truncated at the output token cap."""
        fake = _client(text="## Partial\nbody cut off", stop_reason="max_tokens")
        with pytest.raises(ValueError, match="truncated"):
            enrich("raw", api_key="dummy", client=fake)  # ty: ignore[invalid-argument-type]

    def test_raises_value_error_on_empty_content(self) -> None:
        """enrich() raises ValueError when the response has no content blocks."""
        fake = _client(content=[])
        with pytest.raises(ValueError, match="no content blocks"):
            enrich("raw", api_key="dummy", client=fake)  # ty: ignore[invalid-argument-type]

    def test_raises_type_error_on_non_text_block(self) -> None:
        """enrich() raises TypeError when the first block is not a text block."""
        thinking = anthropic.types.ThinkingBlock(type="thinking", thinking="hmm", signature="sig")
        fake = _client(content=[thinking])
        with pytest.raises(TypeError, match="not a text block"):
            enrich("raw", api_key="dummy", client=fake)  # ty: ignore[invalid-argument-type]

    def test_raises_on_empty_text(self) -> None:
        """enrich() raises when the text block is blank — bad output, not a passthrough."""
        fake = _client(text="   \n  ")
        with pytest.raises(ValueError, match="empty"):
            enrich("raw", api_key="dummy", client=fake)  # ty: ignore[invalid-argument-type]


# ---------------------------------------------------------------------------
# Provider tests (glyde.api.enrich.get_enricher)
# ---------------------------------------------------------------------------


class TestGetEnricher:
    """get_enricher returns None for a blank key and a callable for a real one."""

    def test_returns_none_when_no_key(self) -> None:
        """get_enricher returns None when anthropic_api_key is None."""
        settings = Settings(anthropic_api_key=None)
        assert get_enricher(settings) is None

    def test_returns_none_when_key_is_blank(self) -> None:
        """get_enricher treats an empty/whitespace key as absent (no doomed client)."""
        assert get_enricher(Settings(anthropic_api_key="")) is None
        assert get_enricher(Settings(anthropic_api_key="   ")) is None

    def test_returns_callable_when_key_present(self) -> None:
        """get_enricher returns a callable when anthropic_api_key is set."""
        settings = Settings(anthropic_api_key="sk-test-key")
        enricher = get_enricher(settings)
        assert callable(enricher)


# ---------------------------------------------------------------------------
# Gate logic tests via compose_digest
# ---------------------------------------------------------------------------


class TestComposeEnrichGate:
    """compose_digest enriches only when enrich=True AND enricher AND no structure."""

    def _plain_req(self, *, enrich_flag: bool = True) -> ComposeRequest:
        """Return a request with plain unstructured text (no Glyde markers)."""
        return ComposeRequest(
            name="test",
            text="a raw log line with no structure",
            segments=None,
            source_kind="cli",
            enrich=enrich_flag,
        )

    def _structured_req(self) -> ComposeRequest:
        """Return a request whose text already carries Glyde structure markers."""
        return ComposeRequest(
            name="structured",
            text="## Heading\nAlready structured.",
            segments=None,
            source_kind="cli",
            enrich=True,
        )

    def test_enriches_when_flag_key_and_no_structure(self) -> None:
        """compose_digest calls the enricher when all three conditions hold."""
        called: list[str] = []

        def _spy(text: str) -> str:
            called.append(text)
            return "## Enriched\nresult"

        store = InMemoryDigestStore()
        digest = compose_digest(self._plain_req(enrich_flag=True), _deps(store, enricher=_spy))
        assert called, "enricher must be called for plain unstructured text"
        assert digest.meta.provenance.enriched is True

    def test_skips_enricher_when_enrich_flag_false(self) -> None:
        """compose_digest skips the enricher when enrich=False even if one is provided."""
        called: list[str] = []

        def _spy(text: str) -> str:
            called.append(text)
            return "## Enriched\nresult"

        store = InMemoryDigestStore()
        compose_digest(self._plain_req(enrich_flag=False), _deps(store, enricher=_spy))
        assert not called, "enricher must not be called when enrich=False"

    def test_skips_enricher_when_none(self) -> None:
        """compose_digest uses deterministic parse when no enricher is supplied."""
        store = InMemoryDigestStore()
        digest = compose_digest(self._plain_req(enrich_flag=True), _deps(store, enricher=None))
        assert digest.meta.provenance.enriched is False

    def test_skips_enricher_when_text_has_structure(self) -> None:
        """compose_digest skips enrichment when the text already has structure markers."""
        called: list[str] = []

        def _spy(text: str) -> str:
            called.append(text)
            return "## Enriched\nresult"

        store = InMemoryDigestStore()
        compose_digest(self._structured_req(), _deps(store, enricher=_spy))
        assert not called, "enricher must not be called when text has structure markers"

    def test_falls_back_to_raw_text_when_enricher_raises(self) -> None:
        """compose_digest falls back to deterministic parse when the enricher fails."""

        def _fail(text: str) -> str:
            raise RuntimeError("simulated API failure")

        store = InMemoryDigestStore()
        digest = compose_digest(self._plain_req(enrich_flag=True), _deps(store, enricher=_fail))
        # Falls back gracefully — the digest is stored and enriched flag is False.
        assert digest.meta.provenance.enriched is False
        assert len(digest.segments) > 0

    def test_falls_back_through_the_real_adapter_on_bad_output(self) -> None:
        """A truncated adapter response surfaces as a graceful deterministic fallback.

        Drives the real ``enrich`` adapter (via a fake client) through
        ``compose_digest`` to prove the adapter's bad-output guard reaches the
        try/except fallback rather than persisting partial content.
        """
        fake = _client(text="## Partial", stop_reason="max_tokens")

        def _adapter_enricher(text: str) -> str:
            return enrich(text, api_key="dummy", client=fake)  # ty: ignore[invalid-argument-type]

        store = InMemoryDigestStore()
        digest = compose_digest(
            self._plain_req(enrich_flag=True), _deps(store, enricher=_adapter_enricher)
        )
        assert digest.meta.provenance.enriched is False
        assert len(digest.segments) > 0
