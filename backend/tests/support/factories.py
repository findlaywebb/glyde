"""Factory builders and pinned golden constants for tests.

Prefer these over fixture chains: a test overrides only the field under test and
inherits sane defaults for the rest, so the intent of each test is local and
obvious. ``ts`` is the single pinned canonical instant every frozen-time test
stamps.
"""

from __future__ import annotations

from glyde.core import Record

_FROZEN_TS = "2025-01-01T00:00:00+00:00"


def ts() -> str:
    """Return the single pinned canonical UTC instant used by frozen-time tests."""
    return _FROZEN_TS


def record(
    *,
    id: str = "rec-1",  # noqa: A002 - mirrors the domain field name on purpose
    name: str = "example",
    created_at: str | None = None,
) -> Record:
    """Build a ``Record`` with overridable fields; ``created_at`` defaults to ``ts()``."""
    return Record(id=id, name=name, created_at=created_at or ts())
