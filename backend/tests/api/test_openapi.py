"""OpenAPI surface tests: the drift gate, named seam members, and the union marker.

The committed ``docs/schemas/openapi.json`` is the source of truth the frontend's
``schema.d.ts`` is generated from. The drift test regenerates and compares it
byte-for-byte. The seam tests pin the named wire members the reader units import
and the discriminated-union shape the typed-seam turns on — asserted on the
exported OpenAPI JSON (``openapi-typescript`` collapses ``oneOf`` and ``anyOf``
into the same TS union, so the ``.d.ts`` cannot prove it).
"""

import json

import pytest
from support import REPO_ROOT

from glyde.api.app import create_app
from glyde.api.openapi_doc import canonical_openapi_json

_ARTIFACT = REPO_ROOT / "docs" / "schemas" / "openapi.json"

_NAMED_MEMBERS = (
    "TokenView",
    "ProseSegmentView",
    "PauseView",
    "BlockView",
    "DigestView",
    "DigestListItemView",
    "PreferencesView",
)


def test_app_exposes_the_expected_paths() -> None:
    """The OpenAPI document advertises the digest, preferences, and liveness surfaces."""
    paths = create_app().openapi()["paths"]
    for path in ("/digests", "/digests/{slug}", "/preferences", "/healthz"):
        assert path in paths


def test_committed_openapi_matches_the_app() -> None:
    """The committed docs/schemas/openapi.json equals the freshly generated document."""
    if not _ARTIFACT.exists():
        pytest.skip("run `uv run glyde export-openapi` to create the committed artifact")
    assert _ARTIFACT.read_text(encoding="utf-8") == canonical_openapi_json()


def test_named_seam_members_present() -> None:
    """The seven named wire members the reader units import are in components.schemas."""
    schemas = create_app().openapi()["components"]["schemas"]
    for member in _NAMED_MEMBERS:
        assert member in schemas, f"missing named schema member: {member}"


def test_segment_union_is_discriminated_oneof() -> None:
    """DigestView.segments.items is a oneOf of named refs with a `type` discriminator."""
    if not _ARTIFACT.exists():
        pytest.skip("run `uv run glyde export-openapi` to create the committed artifact")
    document = json.loads(_ARTIFACT.read_text(encoding="utf-8"))
    items = document["components"]["schemas"]["DigestView"]["properties"]["segments"]["items"]
    assert "oneOf" in items
    assert "anyOf" not in items
    assert items["discriminator"]["propertyName"] == "type"
    assert items["discriminator"]["mapping"]
