"""``compose_digest`` — the one composition the CLI and the route share.

Key types:
- ``ComposeRequest`` — the inbound digest request (name, text or segments,
  provenance fields, tags, enrich flag).
- ``ComposeDeps`` — the injected seams (store, the stamped ``now``, the id and
  slug minters, and an optional enricher).
- ``compose_digest`` — parse/segment the input, mint id + slug, stamp time,
  derive the counts, build the ``Digest``, persist it, and return it.

An MCP ingest path (no consumer yet) is a thin wrapper over this same call.

What this module does NOT do:
- No HTTP and no CLI parsing — it adapts a request bundle to the store. The clock,
  id, and slug arrive as injected callables; nothing here reads the environment.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal

from pydantic import TypeAdapter

from glyde.core import Digest, DigestMeta, Provenance, Segment, UnknownDigestError
from glyde.core.derive import BASELINE_WPM, content_sha, count_tokens, estimate_reading_ms
from glyde.core.parsing import parse_glyde_markdown

if TYPE_CHECKING:
    from collections.abc import Callable

    from glyde.api.enrich import Enricher
    from glyde.core import DigestStore

logger = logging.getLogger(__name__)

_SEGMENTS = TypeAdapter(list[Segment])
_STRUCTURE_MARKERS = ("#", "```", "|", "![", "$$", ":::", ">", "-", "*", "+")


@dataclass(frozen=True)
class ComposeRequest:
    """An inbound digest request; exactly one of ``text`` / ``segments`` is set."""

    name: str
    text: str | None
    segments: list[Segment] | None
    source_kind: Literal["agent", "file", "cli", "paste", "pipe", "api"]
    origin: str | None = None
    producer: str | None = None
    ingested_via: Literal["cli", "api", "mcp"] = "cli"
    tags: list[str] = field(default_factory=list)
    enrich: bool = False


@dataclass(frozen=True)
class ComposeDeps:
    """The injected seams ``compose_digest`` needs (store, clock, minters)."""

    store: DigestStore
    now: str
    new_id: Callable[[], str]
    new_slug: Callable[[Callable[[str], bool]], str]
    enricher: Enricher | None = None


def _has_structure(text: str) -> bool:
    """Return True if any line opens with a Glyde-Markdown structure marker."""
    return any(line.strip().startswith(_STRUCTURE_MARKERS) for line in text.splitlines())


def _slug_taken(store: DigestStore, slug: str) -> bool:
    """Return True if ``slug`` already resolves to a stored digest."""
    try:
        store.get_by_slug(slug)
    except UnknownDigestError:
        return False
    return True


def compose_digest(req: ComposeRequest, deps: ComposeDeps) -> Digest:
    """Build, persist, and return a ``Digest`` from ``req`` using ``deps``.

    Enriches raw text only when requested, an enricher is provided, and the text
    has no structure markers (best-effort; a failure falls back to the raw text).
    Parses text to segments (else uses the supplied segments), mints id + slug,
    stamps time, derives the counts, persists, and returns the digest.

    Args:
        req: The inbound request bundle.
        deps: The injected store, clock, and minters.

    Returns:
        The persisted ``Digest``.

    Raises:
        DuplicateSlugError: If the minted slug clashes on insert.
    """
    text = req.text
    enriched = False
    if req.enrich and deps.enricher is not None and text is not None and not _has_structure(text):
        try:
            enriched_text = deps.enricher(text)
        except Exception:  # noqa: BLE001 - best-effort; fall back to the raw deterministic parse
            logger.warning("enrichment failed; using the deterministic parser")
        else:
            text = enriched_text
            enriched = True

    if text is not None:
        segments = parse_glyde_markdown(text)
        source = text
    else:
        segments = list(req.segments or [])
        source = _SEGMENTS.dump_json(segments).decode("utf-8")

    token_count = count_tokens(segments)
    meta = DigestMeta(
        id=deps.new_id(),
        slug=deps.new_slug(lambda candidate: _slug_taken(deps.store, candidate)),
        name=req.name,
        provenance=Provenance(
            source_kind=req.source_kind,
            origin=req.origin,
            producer=req.producer,
            ingested_via=req.ingested_via,
            enriched=enriched,
        ),
        created_at=deps.now,
        token_count=token_count,
        est_reading_ms=estimate_reading_ms(token_count, BASELINE_WPM),
        content_sha=content_sha(source),
        tags=list(req.tags),
    )
    digest = Digest(meta=meta, segments=segments)
    deps.store.add(digest)
    return digest
