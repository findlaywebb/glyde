"""Canonical OpenAPI document export — the frontend type seam's source of truth.

Key callables:
- ``canonical_openapi_json`` — serialise ``create_app().openapi()`` to a stable,
  sorted JSON string. This backs the committed ``docs/schemas/openapi.json``
  artifact from which ``openapi-typescript`` generates the frontend's
  ``schema.d.ts``; the same function backs the drift test, so both sides compare
  byte-for-byte.

What this module does NOT do:
- No file IO and no server — the CLI ``export-openapi`` command writes the bytes
  and the drift test reads them; this only produces the canonical string.

Invariants:
- Deterministic output: sorted keys, 2-space indent, trailing newline, no ASCII
  escaping — so a regenerate-and-compare drift gate sees only real schema change,
  never serialisation noise.
"""

from __future__ import annotations

import json

from glyde.api.app import create_app


def canonical_openapi_json() -> str:
    """Return the app's OpenAPI document as canonical, stable JSON.

    Returns:
        The OpenAPI schema serialised with sorted keys, 2-space indentation, no
        non-ASCII escaping, and a trailing newline — byte-stable across runs so it
        can back the committed-artifact drift gate.
    """
    document = create_app().openapi()
    return json.dumps(document, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
