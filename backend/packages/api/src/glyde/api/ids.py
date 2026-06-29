"""Id minting — the api layer's single source of new ids.

``core`` and ``adapters`` never import ``uuid`` (enforced by the purity
architecture test); ids are born here and travel inward as arguments. Keeping
the one mint site in a named module makes "where do ids come from" answerable in
one read.

Key callables:
- ``new_id`` — return a fresh opaque id string (a v4 UUID).
"""

from __future__ import annotations

import uuid


def new_id() -> str:
    """Return a fresh opaque id (a v4 UUID string)."""
    return str(uuid.uuid4())
