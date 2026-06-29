"""The FastAPI application factory: routers, lifespan, and the error handler.

Key callables:
- ``create_app`` — build the app: mount every router, register the ONE
  store-error exception handler shared by all routes, and wire the lifespan that
  configures logging and runs migrations at startup.

What this module does NOT do:
- No per-route error handling — the single registered handler turns a
  ``StoreError`` into the ``{code, message}`` body with the mapped status.
- No business logic and no schema definitions — those live in the routes and
  ``schemas``.

Invariants:
- The store-error translation is registered ONCE; routes never duplicate it.
- The lifespan configures logging and runs ``bootstrap_migrations`` before the
  app serves, so every request sees a current schema. ASGITransport-based tests
  do NOT run the lifespan — their fixtures migrate the tmp database themselves.
- Same-origin serving: the API is reached under ``/api`` through a stripped-prefix
  proxy (the SvelteKit ``hooks.server.ts`` front door + the dev Vite proxy).
  ``root_path`` makes ``/api/docs`` resolve ``/api/openapi.json``; the explicit
  ``servers`` is what lands in the in-process ``create_app().openapi()`` the export
  CLI and the drift test read. Path keys stay bare — the proxy strips ``/api``. The
  app ships no CORS: every caller is same-origin.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from glyde.api.deps import bootstrap_migrations
from glyde.api.logging_config import setup_logging
from glyde.api.routes import meta_router, records_router
from glyde.api.schemas import Rejection
from glyde.api.settings import get_settings
from glyde.core.ports import StoreError

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

logger = logging.getLogger(__name__)

# Map each store error code to an HTTP status. Unlisted codes fall back to 409
# (a conflict the client can resolve) rather than a 500 — a known rejection is
# never a server fault.
_STATUS_BY_CODE: dict[str, int] = {
    "unknown_record": 404,
    "duplicate_record": 409,
}
_DEFAULT_STATUS = 409


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Configure logging and run migrations so every request sees a current schema."""
    settings = get_settings()
    setup_logging()
    applied = bootstrap_migrations(settings)
    logger.info("startup complete: %d migration(s) applied", applied)
    yield


def _store_error_response(exc: StoreError) -> JSONResponse:
    """Render a ``StoreError`` as the ``{code, message}`` body + mapped status."""
    status = _STATUS_BY_CODE.get(exc.code, _DEFAULT_STATUS)
    body = Rejection(code=exc.code, message=str(exc) or exc.code)
    return JSONResponse(status_code=status, content=body.model_dump())


def create_app() -> FastAPI:
    """Build the Glyde FastAPI app with routers, lifespan, and the error handler.

    Mounts the read/write routers, registers the single store-error exception
    handler (so every route shares one translation), and wires the
    logging-and-migration lifespan.

    Returns:
        The configured ``FastAPI`` application.
    """
    app = FastAPI(
        title="Glyde",
        summary="Glyde API — a typed surface used identically by the UI and by agents.",
        lifespan=_lifespan,
        root_path="/api",
        servers=[{"url": "/api"}],
    )

    @app.exception_handler(StoreError)
    async def _on_store_error(_: Request, exc: StoreError) -> JSONResponse:
        """Translate a store error raised by any route into the wire body."""
        return _store_error_response(exc)

    app.include_router(meta_router)
    app.include_router(records_router)
    return app
