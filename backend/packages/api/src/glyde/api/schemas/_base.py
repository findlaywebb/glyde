"""The shared base for every api-surface schema: frozen, extra-forbidding.

Key types:
- ``ApiModel`` — the one ``BaseModel`` config every request and response schema
  inherits: ``frozen=True`` (wire shapes are immutable once parsed/built) and
  ``extra="forbid"`` (an unrecognised field is a 422, never silently dropped).

Defining it once keeps the api surface consistent and makes the "reject unknown
fields" guarantee a single decision rather than many copies.

``from_attributes=True`` enables the object-to-object projection path
(``View.model_validate(domain_model)``) for response views that mirror a core
model; it is inert for request schemas, which validate from JSON dicts.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ApiModel(BaseModel):
    """Frozen, extra-forbidding base for every api-surface projection and request."""

    model_config = ConfigDict(frozen=True, extra="forbid", from_attributes=True)
