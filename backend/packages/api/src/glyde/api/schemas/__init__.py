"""API-surface request/response schemas — projections of ``glyde.core`` models.

These are the wire shapes the frontend's ``schema.d.ts`` and every agent
integration calcify around. They are deliberately separate from the core domain
models (``backend/CLAUDE.md``): a response schema is a narrowed projection that
never leaks fields the surface must not expose, and a request schema may differ
from the domain model it builds.

Key types:
- ``Rejection`` — the ``{code, message}`` error body every store rejection maps to.
- ``RecordView`` — the read projection of a ``Record``.
- ``CreateRecordRequest`` — the create-a-record request body.

What this module does NOT do:
- No clock, no storage, no id minting — pure schema definitions.

Invariants:
- Every public field carries a ``description`` (enforced by an architecture test):
  agents read these straight from the OpenAPI schema.
"""

from glyde.api.schemas.records import CreateRecordRequest, RecordView
from glyde.api.schemas.results import Rejection

__all__ = ["CreateRecordRequest", "RecordView", "Rejection"]
