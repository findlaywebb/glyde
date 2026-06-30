"""Tests for the ``glyde add`` CLI command's printed reader URL.

Proves the handoff URL uses the LAN-door port (``settings.lan_port``) and not
the FastAPI loopback port (``settings.port``), and that it uses the LAN host
(``settings.lan_host``) and not the FastAPI bind host (``settings.host``).
All four fields are pinned to distinct sentinels so any wrong-field regression
is caught unambiguously.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from typer.testing import CliRunner

from glyde.api.cli import app
from glyde.api.settings import get_settings

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

_RUNNER = CliRunner()

# Distinct sentinel values — the test catches whichever wrong field appears.
_LAN_HOST = "10.0.0.1"  # LAN front-door host; must appear in the printed URL
_FASTAPI_HOST = "10.0.0.2"  # FastAPI loopback bind host; must NOT appear
_LAN_PORT = 54321  # SvelteKit node door; must appear in the printed URL
_FASTAPI_PORT = 54322  # FastAPI loopback bind; must NOT appear


@pytest.fixture()
def _clear_settings_cache() -> Iterator[None]:
    """Clear the settings LRU cache before and after each test."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


class TestAddReaderUrl:
    """Tests for the handoff URL emitted by ``glyde add``."""

    def test_printed_url_uses_lan_door_host_and_port(
        self, tmp_path: Path, _clear_settings_cache: None
    ) -> None:
        """The add command prints the reader URL on the LAN host and port, not the FastAPI loopback."""
        env = {
            "GLYDE_DB_PATH": str(tmp_path / "glyde.db"),
            "GLYDE_LAN_HOST": _LAN_HOST,
            "GLYDE_HOST": _FASTAPI_HOST,
            "GLYDE_LAN_PORT": str(_LAN_PORT),
            "GLYDE_PORT": str(_FASTAPI_PORT),
        }
        result = _RUNNER.invoke(app, ["add", "--name", "test-digest", "hello world"], env=env)
        assert result.exit_code == 0, result.output
        assert f"{_LAN_HOST}:{_LAN_PORT}/d/" in result.output
        assert _FASTAPI_HOST not in result.output
        assert f":{_FASTAPI_PORT}/d/" not in result.output
