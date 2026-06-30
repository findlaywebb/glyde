"""HTTP routers: the digest surface, preferences, liveness, and the LAN scaffold.

Key types:
- ``digests_router`` — ``POST/GET /digests``, ``GET /digests/{slug}``.
- ``preferences_router`` — ``GET/PUT /preferences``.
- ``meta_router`` — ``GET /healthz`` liveness.
- ``lan_router`` — a route-less scaffold (zero path operations) the LAN unit fills.
- ``records_router`` — the template example surface (transitional).

What this module does NOT do:
- No app construction (``app.create_app`` mounts these and registers the
  store-error handler) and no per-route store-error translation.

Invariants:
- Every route declares ``summary`` and ``description``; the OpenAPI schema is the
  contract agents read.
"""

from glyde.api.routes.digests import digests_router
from glyde.api.routes.lan import lan_router
from glyde.api.routes.meta import meta_router
from glyde.api.routes.preferences import preferences_router
from glyde.api.routes.records import records_router

__all__ = [
    "digests_router",
    "lan_router",
    "meta_router",
    "preferences_router",
    "records_router",
]
