"""OpenAPI surface tests, including the committed-artifact drift gate.

The committed ``docs/schemas/openapi.json`` is the source of truth the frontend's
``schema.d.ts`` is generated from. This test regenerates the canonical document
and compares it byte-for-byte, so a backend schema change that wasn't re-exported
fails CI. On a fresh scaffold the artifact does not exist yet — run
``uv run glyde export-openapi`` once to create it; until then the drift test
skips.
"""

import pytest
from support import REPO_ROOT

from glyde.api.app import create_app
from glyde.api.openapi_doc import canonical_openapi_json

_ARTIFACT = REPO_ROOT / "docs" / "schemas" / "openapi.json"


def test_app_exposes_the_expected_paths() -> None:
    """The OpenAPI document advertises the records surface and the liveness probe."""
    paths = create_app().openapi()["paths"]
    assert "/records" in paths
    assert "/records/{record_id}" in paths
    assert "/healthz" in paths


def test_committed_openapi_matches_the_app() -> None:
    """The committed docs/schemas/openapi.json equals the freshly generated document."""
    if not _ARTIFACT.exists():
        pytest.skip("run `uv run glyde export-openapi` to create the committed artifact")
    assert _ARTIFACT.read_text(encoding="utf-8") == canonical_openapi_json()
