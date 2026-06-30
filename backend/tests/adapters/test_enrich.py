"""Tests for the HAIKU enrich path: adapter, provider, and compose_digest gate logic.

Covers:
- ``glyde.adapters.enrich.enrich`` — the Anthropic adapter (via a hand-written
  fake client; no real API call).
- ``glyde.api.enrich.get_enricher`` — key-presence gate (None vs callable).
- ``compose_digest`` enrich gate — enriches only when enrich=True AND an enricher
  is present AND the text has no detected structure; falls back gracefully on any
  failure.

No ``unittest.mock`` or ``pytest_mock`` is used. The Anthropic client is replaced
by a hand-written fake that constructs real ``anthropic.types`` objects so
``isinstance`` checks inside the adapter pass.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import anthropic

if TYPE_CHECKING:
    from collections.abc import Callable
import anthropic.types
import pytest
from support.memory_store import InMemoryDigestStore

from glyde.adapters.enrich import enrich
from glyde.api.compose import ComposeDeps, ComposeRequest, compose_digest
from glyde.api.enrich import get_enricher
from glyde.api.settings import Settings

# ---------------------------------------------------------------------------
# Hand-written fake Anthropic client (real anthropic.types objects)
# ---------------------------------------------------------------------------


class _FakeMessages:
    """Fake Anthropic messages resource returning a canned text response."""

    def __init__(self, return_text: str) -> None:
        """Store the text that ``create`` will return."""
        self._return_text = return_text

    def create(self, **_kwargs: object) -> anthropic.types.Message:
        """Return a canned ``Message`` with a single TextBlock."""
        return anthropic.types.Message(
            id="fake-msg-id",
            content=[anthropic.types.TextBlock(type="text", text=self._return_text)],
            model="claude-haiku-4-5",
            role="assistant",
            type="message",
            usage=anthropic.types.Usage(input_tokens=1, output_tokens=1),
        )


class _FakeClient:
    """Fake Anthropic client exposing only the ``messages.create`` surface."""

    def __init__(self, return_text: str = "## Result\nA result.") -> None:
        """Configure the text the fake messages resource will return."""
        self.messages = _FakeMessages(return_text)


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
    """The Anthropic adapter returns the text block from the fake client response."""

    def test_returns_text_from_canned_response(self) -> None:
        """enrich() extracts and returns the TextBlock text from the fake client."""
        fake = _FakeClient(return_text="## Structured\nbody text")
        result = enrich("raw input", api_key="dummy", client=fake)  # ty: ignore[invalid-argument-type]
        assert result == "## Structured\nbody text"

    def test_raises_value_error_on_empty_content(self) -> None:
        """enrich() raises ValueError when the response has no content blocks."""

        class _EmptyMessages:
            def create(self, **_kwargs: object) -> anthropic.types.Message:
                """Return a Message with no content."""
                return anthropic.types.Message(
                    id="empty-msg",
                    content=[],
                    model="claude-haiku-4-5",
                    role="assistant",
                    type="message",
                    usage=anthropic.types.Usage(input_tokens=1, output_tokens=0),
                )

        class _EmptyClient:
            messages = _EmptyMessages()

        with pytest.raises(ValueError, match="no content blocks"):
            enrich("raw", api_key="dummy", client=_EmptyClient())  # ty: ignore[invalid-argument-type]


# ---------------------------------------------------------------------------
# Provider tests (glyde.api.enrich.get_enricher)
# ---------------------------------------------------------------------------


class TestGetEnricher:
    """get_enricher returns None without a key and a callable with one."""

    def test_returns_none_when_no_key(self) -> None:
        """get_enricher returns None when anthropic_api_key is absent."""
        settings = Settings(anthropic_api_key=None)
        assert get_enricher(settings) is None

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
