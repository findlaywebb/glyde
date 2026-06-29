"""Result and rejection envelopes for the api surface.

Key types:
- ``Rejection`` — the ``{code, message}`` body every store rejection maps to. The
  ``code`` is the stable, machine-readable contract a client (UI or agent)
  branches on; ``message`` is human-facing detail.
"""

from __future__ import annotations

from pydantic import Field

from glyde.api.schemas._base import ApiModel


class Rejection(ApiModel):
    """The error body returned when the store rejects an operation."""

    code: str = Field(description="Stable, machine-readable rejection code.")
    message: str = Field(description="Human-facing detail about the rejection.")
