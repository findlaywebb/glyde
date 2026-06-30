"""Application settings — the one place the environment is read, injected inward.

Key types:
- ``Settings`` — a ``pydantic-settings`` ``BaseSettings`` reading the ``GLYDE_``
  prefixed environment. It carries the full v1 surface up front (db path, the
  FastAPI bind, the LAN front-door + HTTPS knobs, the Anthropic key) so no later
  unit re-edits this file; LAN and the enrich path read fields declared here.
- ``get_settings`` — the ``@lru_cache`` provider FastAPI injects via ``Depends``
  and the CLI calls directly. Tests override it through
  ``app.dependency_overrides`` and clear the cache with
  ``get_settings.cache_clear()``.

What this module does NOT do:
- No clock reads, no storage access, no migrations — it only carries config.
- No business logic. ``Settings`` is the one place the environment is read;
  ``glyde.core`` never reads it (config is injected inward). The Anthropic key
  and the LAN token are injected from here, never read in ``core``/``adapters``.

Invariants:
- The database lives in the OS app-data dir (``platformdirs.user_data_dir``);
  ``GLYDE_DB_PATH`` overrides it — never today's CWD.
- ``db_path`` is a ``pathlib.Path``; ``host``/``port`` configure the loopback
  FastAPI bind; ``lan_*`` configure the adapter-node LAN front door.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import platformdirs
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_APP_NAME = "glyde"


def _default_db_path() -> Path:
    """Return the default database path under the OS app-data dir."""
    return Path(platformdirs.user_data_dir(_APP_NAME)) / "glyde.db"


class Settings(BaseSettings):
    """Runtime configuration read from the ``GLYDE_`` prefixed environment.

    Construct directly (with overrides) in tests, or obtain the cached singleton
    via ``get_settings``. The LAN and enrich fields are declared but unused by
    the foundation; later units read them without re-editing this file.
    """

    model_config = SettingsConfigDict(env_prefix="GLYDE_", frozen=True)

    db_path: Path = Field(default_factory=_default_db_path)
    host: str = "127.0.0.1"
    port: int = 8000
    lan_host: str = "127.0.0.1"
    lan_port: int = 3000
    lan_token: str | None = None
    lan_https: bool = False
    lan_cert_path: Path | None = None
    lan_key_path: Path | None = None
    anthropic_api_key: str | None = None

    @property
    def data_dir(self) -> Path:
        """Return the OS app-data directory Glyde stores its data under."""
        return Path(platformdirs.user_data_dir(_APP_NAME))


@lru_cache
def get_settings() -> Settings:
    """Return the cached ``Settings`` singleton (the dependency-injection seam).

    FastAPI injects this via ``Depends``; the CLI calls it directly. Cached so
    every request shares one instance; tests override it through
    ``app.dependency_overrides`` and clear the cache with
    ``get_settings.cache_clear()`` in teardown.
    """
    return Settings()
