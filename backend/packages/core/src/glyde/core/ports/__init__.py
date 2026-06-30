"""Port interfaces — the abstract seams concrete adapters implement.

A port is an abstract interface (ABC) that imports only from ``glyde.core``;
every concrete adapter in ``glyde.adapters`` must implement one, and the
architecture tests enforce that. This package re-exports the port surface:
``DigestStore`` (the digest + preferences persistence port) and the shared error
taxonomy.

Rule of three: new ports are NOT defined speculatively — each arrives here with
its first real consumer (prefer duplication over the wrong abstraction).
"""

from glyde.core.ports.digest_store import DigestStore
from glyde.core.ports.errors import (
    DuplicateSlugError,
    StoreError,
    UnknownDigestError,
)

__all__ = [
    "DigestStore",
    "DuplicateSlugError",
    "StoreError",
    "UnknownDigestError",
]
