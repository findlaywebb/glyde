"""HTTP routers: the read surface and the example records endpoints.

Key types:
- ``meta_router`` — ``GET /healthz`` liveness.
- ``records_router`` — the example CRUD-ish surface (``GET /records``,
  ``POST /records``, ``GET /records/{id}``).

What this module does NOT do:
- No app construction (``app.create_app`` mounts these routers and registers the
  store-error handler) and no store-error translation per route — one app-level
  exception handler owns that.
- No business logic — routes adapt HTTP to the store and the clock/mint seams.

Invariants:
- Every route declares ``summary`` and ``description``; the OpenAPI schema is the
  contract agents read.
"""

from glyde.api.routes.meta import meta_router
from glyde.api.routes.records import records_router

__all__ = ["meta_router", "records_router"]
