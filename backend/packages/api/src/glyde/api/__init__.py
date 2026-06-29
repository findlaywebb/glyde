"""The FastAPI application — Glyde's only serving surface.

This layer owns the app factory, routers, request/response schemas (API-surface
projections of ``glyde.core`` models, kept separate from them), settings, and
the CLI. It is the one place the clock is read, ids are minted, and the
environment is read.

What it does NOT do: no business logic (delegate to ``glyde.core``), no direct
storage access (go through adapters). The store is the source of truth.

Invariants:
- Timestamps are server-stamped (``clock.canonical_now``); clients never supply them.
- Every route declares ``summary`` and ``description`` — the OpenAPI schema is
  the contract agents read.

Public surface:
- ``create_app`` — the FastAPI application factory (mounts routers, registers the
  store-error handler, runs migrations and configures logging in its lifespan).
- ``Settings`` / ``get_settings`` — runtime configuration and its injection seam.
"""

from glyde.api.app import create_app
from glyde.api.settings import Settings, get_settings

__all__ = ["Settings", "create_app", "get_settings"]
