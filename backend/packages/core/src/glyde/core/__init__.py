"""Glyde's domain kernel: models, ports, and pure logic.

This layer owns the domain models (the Digest IR — see ``glyde.core.models``),
the port interfaces every adapter implements (see ``glyde.core.ports``), and the
pure derivation helpers (see ``glyde.core.derive``) and the Glyde-Markdown parser
(see ``glyde.core.parsing``). The Digest IR is the one typed contract every layer
codes against. ``Record`` is the template's transitional example model, retained
only until the IR replaces it end to end.

What it does NOT do: no I/O of any kind. No framework imports (FastAPI, DB
drivers, HTTP clients), no filesystem access, no ``os.environ`` — configuration
is injected by callers. Enforced by import-linter and the architecture tests,
not convention.

Invariants:
- Clock-free and id-free: core never reads the clock and never mints ids/slugs;
  all three arrive as arguments (the api layer stamps time and mints ids/slugs).
- Timestamps are canonical ISO-8601 UTC strings; lexicographic order is
  therefore chronological order.
"""

from glyde.core.models import (
    Block,
    Digest,
    DigestMeta,
    Pause,
    Preferences,
    ProseSegment,
    Provenance,
    ReadingHint,
    Record,
    Segment,
    Token,
)
from glyde.core.ports import (
    DigestStore,
    DuplicateRecordError,
    DuplicateSlugError,
    RecordStore,
    StoreError,
    UnknownDigestError,
    UnknownRecordError,
)

__all__ = [
    "Block",
    "Digest",
    "DigestMeta",
    "DigestStore",
    "DuplicateRecordError",
    "DuplicateSlugError",
    "Pause",
    "Preferences",
    "ProseSegment",
    "Provenance",
    "ReadingHint",
    "Record",
    "RecordStore",
    "Segment",
    "StoreError",
    "Token",
    "UnknownDigestError",
    "UnknownRecordError",
]
