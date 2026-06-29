"""The system's one clock read: a canonical UTC timestamp string.

Key callables:
- ``canonical_now`` — the current instant as a canonical UTC timestamp string
  (``+00:00`` offset, microsecond precision). This is the ONLY place wall-clock
  time enters Glyde; ``core`` and ``adapters`` are clock-free by contract and
  receive every timestamp as an argument.

What this module does NOT do:
- No formatting variants, no parsing, no timezone conversion — it produces the
  single canonical form the domain's timestamp fields accept.
- No id minting.

Invariants:
- The returned string is timezone-aware UTC with a ``+00:00`` offset (never a
  ``Z`` suffix) so it sorts lexicographically in chronological order.
"""

from __future__ import annotations

from datetime import UTC, datetime


def canonical_now() -> str:
    """Return the current UTC instant as a canonical timestamp string.

    The one clock read in the system: route handlers and the CLI obtain ``now``
    here (the api layer stamps time; ``core``/``adapters`` never do) and pass it
    inward as an argument.

    Returns:
        The current instant as a ``+00:00``-offset ISO-8601 string with
        microsecond precision.
    """
    return datetime.now(UTC).isoformat()
