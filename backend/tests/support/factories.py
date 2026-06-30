"""Factory builders and pinned golden constants for tests.

Prefer these over fixture chains: a test overrides only the field under test and
inherits sane defaults for the rest, so the intent of each test is local and
obvious. ``ts`` is the single pinned canonical instant every frozen-time test
stamps.
"""

from __future__ import annotations

from typing import Literal

from glyde.core import (
    Block,
    Digest,
    DigestMeta,
    Pause,
    Preferences,
    ProseSegment,
    Provenance,
    Segment,
    Token,
)

_FROZEN_TS = "2025-01-01T00:00:00+00:00"


def ts() -> str:
    """Return the single pinned canonical UTC instant used by frozen-time tests."""
    return _FROZEN_TS


def words(*texts: str) -> list[Token]:
    """Build a list of ``word`` tokens from raw strings."""
    return [Token(text=text) for text in texts]


def prose(*texts: str, role: Literal["heading", "body", "list_item"] = "body") -> ProseSegment:
    """Build a ``ProseSegment`` from raw word strings (defaults to a body run)."""
    return ProseSegment(role=role, tokens=words(*texts))


def pause(reason: Literal["clause", "sentence", "paragraph", "block_ahead"] = "sentence") -> Pause:
    """Build a ``Pause`` with the given reason."""
    return Pause(reason=reason)


def block(
    kind: Literal["code", "table", "image", "quote", "math", "note"] = "code",
    *,
    content: str = "x = 1",
    lead: str | None = None,
) -> Block:
    """Build a ``Block`` of the given kind with overridable content and lead."""
    return Block(kind=kind, content=content, lead=lead)


def provenance(
    *,
    source_kind: Literal["agent", "file", "cli", "paste", "pipe", "api"] = "cli",
    origin: str | None = None,
) -> Provenance:
    """Build a ``Provenance`` with overridable source kind and origin."""
    return Provenance(source_kind=source_kind, origin=origin)


def digest(
    *,
    id: str = "dig-1",  # noqa: A002 - mirrors the domain field name on purpose
    slug: str = "brave-otter",
    name: str = "example",
    created_at: str | None = None,
    segments: list[Segment] | None = None,
) -> Digest:
    """Build a ``Digest`` with overridable identity, time, and segments."""
    body = segments if segments is not None else [prose("hello", "world")]
    meta = DigestMeta(
        id=id,
        slug=slug,
        name=name,
        provenance=provenance(),
        created_at=created_at or ts(),
        token_count=2,
        est_reading_ms=400,
        content_sha="0" * 64,
    )
    return Digest(meta=meta, segments=body)


def preferences(
    *, owner_id: str = "local", mode: Literal["rsvp", "guided", "fading", "focus"] = "guided"
) -> Preferences:
    """Build a ``Preferences`` with overridable owner and mode."""
    return Preferences(owner_id=owner_id, mode=mode)
