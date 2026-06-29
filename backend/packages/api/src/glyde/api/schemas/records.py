"""Request/response schemas for the records surface — projections of ``Record``.

Key types:
- ``RecordView`` — the read projection of a ``Record`` (built via
  ``RecordView.model_validate(record)``).
- ``CreateRecordRequest`` — the create body. It carries only ``name``; the id and
  ``created_at`` are minted/stamped server-side, never client-supplied.
"""

from __future__ import annotations

from pydantic import Field

from glyde.api.schemas._base import ApiModel


class RecordView(ApiModel):
    """The read-surface projection of a domain ``Record``."""

    id: str = Field(description="Opaque unique id.")
    name: str = Field(description="The record's non-blank name.")
    created_at: str = Field(description="Canonical ISO-8601 UTC creation timestamp.")


class CreateRecordRequest(ApiModel):
    """The body for creating a record; the server mints the id and stamps the time."""

    name: str = Field(min_length=1, description="Human-meaningful, non-blank name.")
