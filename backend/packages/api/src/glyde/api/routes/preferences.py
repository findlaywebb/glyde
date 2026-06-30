"""The preferences surface: read and full-replace per-user reading config.

Key types:
- ``preferences_router`` — ``GET /preferences``, ``PUT /preferences``.

``GET`` returns the stored ``PreferencesView`` for an ``owner_id`` (or the
defaults). ``PUT`` is full-replace: the body becomes the stored row (upsert by
``owner_id``), and because every ``PreferencesView`` field defaults, a partial
body validates and missing fields fall to their defaults.

What this module does NOT do:
- No store-error translation (the app-level handler owns it), no pacing maths.

Invariants:
- The store dependency's annotation is imported at runtime (``# noqa: TC001``):
  FastAPI resolves ``Depends`` annotations via ``get_type_hints`` at runtime.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from glyde.api.deps import get_digest_store
from glyde.api.schemas import PreferencesView
from glyde.core import Preferences
from glyde.core.ports import (  # noqa: TC001 - runtime-needed: FastAPI resolves the Depends annotation
    DigestStore,
)

preferences_router = APIRouter(prefix="/preferences", tags=["preferences"])


@preferences_router.get(
    "",
    response_model=PreferencesView,
    summary="Get preferences",
    description="Return the stored reading preferences for an owner, or the defaults.",
)
def get_preferences(
    store: Annotated[DigestStore, Depends(get_digest_store)],
    owner_id: str = "local",
) -> PreferencesView:
    """Return the reading preferences for ``owner_id`` (defaults if none stored)."""
    return PreferencesView.model_validate(store.get_preferences(owner_id))


@preferences_router.put(
    "",
    response_model=PreferencesView,
    summary="Replace preferences",
    description="Full-replace the owner's reading preferences (upsert) and return them.",
)
def put_preferences(
    body: PreferencesView,
    store: Annotated[DigestStore, Depends(get_digest_store)],
) -> PreferencesView:
    """Upsert the full preferences object by owner_id and return it."""
    prefs = Preferences.model_validate(body.model_dump())
    store.put_preferences(prefs)
    return PreferencesView.model_validate(prefs)
