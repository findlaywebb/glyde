"""Fixtures for the api tests: ASGITransport clients over both store backings.

Time is frozen through the single ``get_now`` override so every route stamps the
same canonical instant — the determinism the no-mocking rule needs. The
``digest_client`` fixture is parametrised over the in-memory fake and the real
SQLite store (which it migrates into a tmp db), so a test runs on both backings.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx
import pytest
from httpx import ASGITransport
from support.factories import ts
from support.memory_store import InMemoryDigestStore

from glyde.adapters.sqlite import apply_migrations
from glyde.api.app import create_app
from glyde.api.deps import get_digest_store, get_now
from glyde.api.settings import Settings, get_settings

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from pathlib import Path


def _frozen_now() -> str:
    """Return the fixed canonical instant every route stamps under test."""
    return ts()


async def _serve(app: object) -> AsyncIterator[httpx.AsyncClient]:
    """Yield an ASGITransport client bound to ``app``."""
    transport = ASGITransport(app=app)  # ty: ignore[invalid-argument-type]
    async with httpx.AsyncClient(transport=transport, base_url="http://glyde.test") as client:
        yield client


def _sqlite_settings(db_path: Path) -> Settings:
    """Migrate a fresh tmp db and return settings pointing at it (cache cleared)."""
    apply_migrations(db_path, backup_stamp="00000000T000000Z")
    get_settings.cache_clear()
    return Settings(db_path=db_path)


def _memory_digest_app() -> object:
    """Build an app over a single in-memory digest store with frozen time."""
    store = InMemoryDigestStore()
    app = create_app()
    app.dependency_overrides[get_digest_store] = lambda: store
    app.dependency_overrides[get_now] = _frozen_now
    return app


def _sqlite_digest_app(db_path: Path) -> object:
    """Build an app over a real migrated, connection-per-request sqlite db."""
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: _sqlite_settings(db_path)
    app.dependency_overrides[get_now] = _frozen_now
    return app


@pytest.fixture(params=["memory", "sqlite"])
async def digest_client(
    request: pytest.FixtureRequest, tmp_path: Path
) -> AsyncIterator[httpx.AsyncClient]:
    """A digest client parametrised over both store backings (memory, then sqlite)."""
    app = (
        _memory_digest_app()
        if request.param == "memory"
        else _sqlite_digest_app(tmp_path / "glyde.db")
    )
    async for served in _serve(app):
        yield served
    get_settings.cache_clear()
