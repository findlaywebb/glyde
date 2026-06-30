"""The digests surface: create, list, and fetch a digest.

Key types:
- ``digests_router`` — ``POST /digests``, ``GET /digests``, ``GET /digests/{slug}``.

HTTP body in -> ``compose_digest`` (parse/segment, mint id + slug, stamp time,
derive counts, persist) -> projected ``DigestView`` out. The list route projects
``DigestListItemView`` (metadata + derived ``counts``) newest-first.

What this module does NOT do:
- No store-error translation (the app-level handler maps ``StoreError`` ->
  ``{code, message}`` + status), no clock/id/slug logic beyond the injected seams.

Invariants:
- The store dependency's annotation is imported at runtime (``# noqa: TC001``):
  FastAPI resolves ``Depends`` annotations via ``get_type_hints`` at runtime.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from pydantic import TypeAdapter

from glyde.api.compose import ComposeDeps, ComposeRequest, compose_digest
from glyde.api.deps import get_digest_store, get_now
from glyde.api.enrich import get_enricher
from glyde.api.ids import new_id
from glyde.api.schemas import (
    CountsView,
    CreateDigestRequest,
    DigestListItemView,
    DigestMetaView,
    DigestView,
)

# Runtime imports: FastAPI resolves these `Depends`/`Settings` annotations via
# get_type_hints at runtime; a TYPE_CHECKING-only import would be mis-read.
from glyde.api.settings import (
    Settings,
    get_settings,
)
from glyde.api.slug import new_slug
from glyde.core import Block, Digest, Segment
from glyde.core.derive import count_tokens
from glyde.core.ports import (  # noqa: TC001
    DigestStore,
)

_CORE_SEGMENTS = TypeAdapter(list[Segment])

digests_router = APIRouter(prefix="/digests", tags=["digests"])


def _to_core_segments(body: CreateDigestRequest) -> list[Segment] | None:
    """Convert a request's wire segments to core segments, or ``None``."""
    if body.segments is None:
        return None
    return _CORE_SEGMENTS.validate_python([segment.model_dump() for segment in body.segments])


def _blocks_by_kind(digest: Digest) -> dict[str, int]:
    """Count a digest's blocks keyed by block kind."""
    counts: dict[str, int] = {}
    for segment in digest.segments:
        if isinstance(segment, Block):
            counts[segment.kind] = counts.get(segment.kind, 0) + 1
    return counts


def _as_list_item(digest: Digest) -> DigestListItemView:
    """Project a digest to a library list item with derived counts."""
    counts = CountsView(words=count_tokens(digest.segments), blocks_by_kind=_blocks_by_kind(digest))
    return DigestListItemView(meta=DigestMetaView.model_validate(digest.meta), counts=counts)


@digests_router.post(
    "",
    response_model=DigestView,
    status_code=status.HTTP_201_CREATED,
    summary="Create a digest",
    description="Parse/segment the input, mint id + slug, stamp time, persist, and return the IR.",
)
def create_digest(
    body: CreateDigestRequest,
    store: Annotated[DigestStore, Depends(get_digest_store)],
    now: Annotated[str, Depends(get_now)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> DigestView:
    """Compose a digest from the request and return its full IR projection."""
    request = ComposeRequest(
        name=body.name,
        text=body.text,
        segments=_to_core_segments(body),
        source_kind=body.source_kind,
        origin=body.origin,
        producer=body.producer,
        ingested_via=body.ingested_via,
        tags=list(body.tags),
        enrich=body.enrich,
    )
    deps = ComposeDeps(
        store=store,
        now=now,
        new_id=new_id,
        new_slug=new_slug,
        enricher=get_enricher(settings),
    )
    return DigestView.model_validate(compose_digest(request, deps))


@digests_router.get(
    "",
    response_model=list[DigestListItemView],
    summary="List digests",
    description="Every digest newest-first, each with metadata and derived shape counts.",
)
def list_digests(
    store: Annotated[DigestStore, Depends(get_digest_store)],
) -> list[DigestListItemView]:
    """Return the library: each digest's metadata plus derived counts, newest-first."""
    return [_as_list_item(digest) for digest in store.list_all()]


@digests_router.get(
    "/{slug}",
    response_model=DigestView,
    summary="Fetch a digest",
    description="Return the full IR for the digest with the given slug, or a 404 rejection.",
)
def get_digest(
    slug: str,
    store: Annotated[DigestStore, Depends(get_digest_store)],
) -> DigestView:
    """Return one digest's full IR by slug (an absent slug maps to 404)."""
    return DigestView.model_validate(store.get_by_slug(slug))
