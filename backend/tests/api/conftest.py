"""Fixtures for the api tests: ASGITransport clients over both store backings.

Time is frozen through the single ``get_now`` override so every route stamps the
same canonical instant — the determinism the no-mocking rule needs. Two client
fixtures share that shape:

- ``memory_client`` overrides ``get_store`` with the verified in-memory fake.
- ``sqlite_client`` migrates a ``tmp_path`` database itself (ASGITransport never
  runs the app lifespan, so nothing else migrates) and overrides ``get_settings``
  to point ``get_store`` at it, clearing the settings cache in teardown.

``client`` is parametrised over both so a test marked with it runs end to end on
each backing.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx
import pytest
from httpx import ASGITransport
from support.factories import ts
from support.memory_store import InMemoryRecordStore

from glyde.adapters.sqlite import apply_migrations
from glyde.api.app import create_app
from glyde.api.deps import get_now, get_store
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


def _memory_app() -> object:
    """Build an app over a single in-memory store double with frozen time."""
    store = InMemoryRecordStore()
    app = create_app()
    app.dependency_overrides[get_store] = lambda: store
    app.dependency_overrides[get_now] = _frozen_now
    return app


def _sqlite_app(db_path: Path) -> object:
    """Build an app over a real migrated, connection-per-request sqlite db.

    Migrates ``db_path`` first (the lifespan never runs under ASGITransport) and
    uses the real connection-per-request ``get_store`` via a ``get_settings``
    override, so the leg exercises the sqlite adapter end to end. Time is frozen.
    """
    apply_migrations(db_path, backup_stamp="00000000T000000Z")
    get_settings.cache_clear()
    settings = Settings(db_path=db_path)
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_now] = _frozen_now
    return app


@pytest.fixture
async def memory_client() -> AsyncIterator[httpx.AsyncClient]:
    """An ASGITransport client over the in-memory store with frozen time."""
    async for client in _serve(_memory_app()):
        yield client


@pytest.fixture
async def sqlite_client(tmp_path: Path) -> AsyncIterator[httpx.AsyncClient]:
    """An ASGITransport client over a real migrated sqlite db with frozen time."""
    async for client in _serve(_sqlite_app(tmp_path / "glyde.db")):
        yield client
    get_settings.cache_clear()


@pytest.fixture(params=["memory", "sqlite"])
async def client(
    request: pytest.FixtureRequest, tmp_path: Path
) -> AsyncIterator[httpx.AsyncClient]:
    """A client parametrised over both store backings (memory, then sqlite)."""
    app = _memory_app() if request.param == "memory" else _sqlite_app(tmp_path / "glyde.db")
    async for served in _serve(app):
        yield served
    get_settings.cache_clear()
