"""Meta read routes: liveness.

Key types:
- ``meta_router`` — ``GET /healthz`` (liveness).

What this module does NOT do:
- No mutation and no store-error translation (the app-level handler owns the latter).
- No readiness/migration probing on ``/healthz`` — it is a pure liveness check;
  the lifespan has already migrated by the time the app serves.

Invariants:
- ``/healthz`` takes no store dependency, so it answers even if the database is
  unreachable (it proves the process is up, not that storage is healthy).
"""

from __future__ import annotations

from fastapi import APIRouter

meta_router = APIRouter(tags=["meta"])


@meta_router.get(
    "/healthz",
    summary="Liveness probe",
    description="Return {status: ok} when the process is serving. No storage access.",
)
def healthz() -> dict[str, str]:
    """Return a static liveness payload."""
    return {"status": "ok"}
