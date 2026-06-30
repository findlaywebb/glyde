"""Domain models — the data shapes the rest of the system speaks.

The Digest IR is the single typed contract every layer codes against: a
``Digest`` is ``DigestMeta`` plus an ordered list of ``Segment`` s, where a
``Segment`` is the discriminated union ``ProseSegment | Pause | Block`` keyed on
``type``. ``Token`` is the streamed prose atom; ``Provenance`` records origin;
``Preferences`` is per-user reading config (never digest content).

One concept per file: ``token``, ``segment``, ``provenance``, ``digest``,
``preferences``. ``Record`` is the template's transitional example model, kept
only until the IR replaces it end to end.

What this package does NOT do: no I/O, no clock reads, no id minting — ``id`` and
``created_at`` arrive from the api layer; derived counts come from
``glyde.core.derive``.
"""

from glyde.core.models.digest import Digest, DigestMeta, ReadingHint
from glyde.core.models.preferences import Preferences
from glyde.core.models.provenance import Provenance
from glyde.core.models.record import Record
from glyde.core.models.segment import Block, Pause, ProseSegment, Segment
from glyde.core.models.token import Token

__all__ = [
    "Block",
    "Digest",
    "DigestMeta",
    "Pause",
    "Preferences",
    "ProseSegment",
    "Provenance",
    "ReadingHint",
    "Record",
    "Segment",
    "Token",
]
