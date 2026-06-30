"""The FastAPI application factory: routers, lifespan, and the error handler.

Key callables:
- ``create_app`` — build the app: mount every router (including the route-less
  ``lan`` scaffold), register the ONE store-error exception handler shared by all
  routes, and wire the lifespan that configures logging and runs migrations.

What this module does NOT do:
- No per-route error handling — the single registered handler turns a
  ``StoreError`` into the ``{code, message}`` body with the mapped status.
- No business logic and no schema definitions — those live in the routes and
  ``schemas``.

Invariants:
- The store-error translation is registered ONCE; routes never duplicate it.
- The lifespan runs ``bootstrap_migrations`` before the app serves. ASGITransport
  tests do NOT run the lifespan — their fixtures migrate the tmp database.
- Same-origin serving under ``/api`` (the SvelteKit proxy strips the prefix);
  ``root_path`` + explicit ``servers`` keep the committed OpenAPI prefix-aware.
  Registering the empty ``lan`` router is OpenAPI-neutral.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from glyde.api.deps import bootstrap_migrations
from glyde.api.logging_config import setup_logging
from glyde.api.routes import (
    digests_router,
    lan_router,
    meta_router,
    preferences_router,
)
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
    "unknown_digest": 404,
    "duplicate_slug": 409,
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
    app.include_router(digests_router)
    app.include_router(preferences_router)
    app.include_router(lan_router)
    return app
