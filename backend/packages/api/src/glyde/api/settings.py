"""Application settings: the db path and bind host/port, injected not read.

Key types:
- ``Settings`` — a ``pydantic-settings`` ``BaseSettings`` reading the ``GLYDE_``
  prefixed environment. The db path and the uvicorn bind host/port are the
  whole surface; add fields as the app grows.
- ``get_settings`` — the ``@lru_cache`` provider FastAPI injects via ``Depends``
  and the CLI calls directly. Tests override it through
  ``app.dependency_overrides`` and clear the cache with
  ``get_settings.cache_clear()``.

What this module does NOT do:
- No clock reads, no storage access, no migrations — it only carries config.
- No business logic. ``Settings`` is the one place the environment is read;
  ``glyde.core`` never reads it (config is injected inward).

Invariants:
- The environment is read ONLY here (``pydantic-settings``); ``core`` and
  ``adapters`` stay environment-free.
- ``db_path`` is a ``pathlib.Path``; ``host``/``port`` configure the uvicorn
  bind in ``cli serve``.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration read from the ``GLYDE_`` prefixed environment.

    The db path is where the SQLite source of truth lives; ``host`` and ``port``
    are the uvicorn bind for ``glyde serve``. Construct directly (with
    overrides) in tests, or obtain the cached singleton via ``get_settings``.
    """

    model_config = SettingsConfigDict(env_prefix="GLYDE_", frozen=True)

    db_path: Path = Path("glyde.db")
    host: str = "127.0.0.1"
    port: int = 8000


@lru_cache
def get_settings() -> Settings:
    """Return the cached ``Settings`` singleton (the dependency-injection seam).

    FastAPI injects this via ``Depends``; the CLI calls it directly. Cached so
    every request shares one instance; tests override it through
    ``app.dependency_overrides`` and clear the cache with
    ``get_settings.cache_clear()`` in teardown.
    """
    return Settings()
