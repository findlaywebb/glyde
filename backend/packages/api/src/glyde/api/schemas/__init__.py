"""API-surface request/response schemas — projections of ``glyde.core`` models.

These are the wire shapes the frontend's ``schema.d.ts`` and every agent
integration calcify around. They are deliberately separate from the core domain
models (``backend/CLAUDE.md``): a response schema is a narrowed projection, and a
request schema may differ from the domain model it builds.

Key types:
- ``Rejection`` — the ``{code, message}`` error body every store rejection maps to.
- The digest surface: ``TokenView``, ``ProseSegmentView``, ``PauseView``,
  ``BlockView`` (the named, discriminated ``SegmentView`` members), ``DigestView``,
  ``DigestListItemView`` (with ``CountsView``), ``DigestMetaView``,
  ``ProvenanceView``, ``ReadingHintView``, and ``CreateDigestRequest``.
- ``PreferencesView`` — the per-user reading config (every field defaulted).

Invariants:
- Every public field carries a ``description`` (bar the ``type`` discriminator),
  enforced by an architecture test: agents read these from the OpenAPI schema.
"""

from glyde.api.schemas.digests import (
    CountsView,
    CreateDigestRequest,
    DigestListItemView,
    DigestMetaView,
    DigestView,
    ProvenanceView,
    ReadingHintView,
)
from glyde.api.schemas.preferences import PreferencesView
from glyde.api.schemas.results import Rejection
from glyde.api.schemas.segments import (
    BlockView,
    PauseView,
    ProseSegmentView,
    SegmentView,
    TokenView,
)

__all__ = [
    "BlockView",
    "CountsView",
    "CreateDigestRequest",
    "DigestListItemView",
    "DigestMetaView",
    "DigestView",
    "PauseView",
    "PreferencesView",
    "ProseSegmentView",
    "ProvenanceView",
    "ReadingHintView",
    "Rejection",
    "SegmentView",
    "TokenView",
]
