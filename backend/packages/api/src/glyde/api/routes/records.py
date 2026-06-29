"""The example records surface: list, create, and fetch a record.

Key types:
- ``records_router`` — ``GET /records``, ``POST /records``, ``GET /records/{id}``.

This is the template's worked example of a typed vertical: HTTP body in →
domain ``Record`` built with a server-minted id and server-stamped time → store
→ projected ``RecordView`` out. Replace it with the real surface.

What this module does NOT do:
- No store-error translation (the app-level handler maps ``StoreError`` →
  ``{code, message}`` + status), no clock/id logic of its own beyond calling the
  injected seams.

Invariants:
- The id is minted (``ids.new_id``) and the time stamped (``get_now``) server-side;
  the client supplies neither.
- The store dependency's annotation is imported at runtime (``# noqa: TC001``):
  FastAPI resolves ``Depends`` annotations via ``get_type_hints`` at runtime, and
  a ``TYPE_CHECKING``-only import would make it mis-read the param as a query field.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status

from glyde.api.deps import get_now, get_store
from glyde.api.ids import new_id
from glyde.api.schemas import CreateRecordRequest, RecordView
from glyde.core import Record

# Runtime import: FastAPI resolves the route's `Depends` annotation via
# get_type_hints; a TYPE_CHECKING-only RecordStore would raise NameError and
# FastAPI would mis-read `store` as a query parameter.
from glyde.core.ports import (
    RecordStore,  # noqa: TC001 - runtime-needed: FastAPI resolves the Depends annotation
)

records_router = APIRouter(prefix="/records", tags=["records"])


@records_router.get(
    "",
    response_model=list[RecordView],
    summary="List records",
    description="Every record, ordered by creation time ascending.",
)
def list_records(store: Annotated[RecordStore, Depends(get_store)]) -> list[RecordView]:
    """Return every record as a read projection."""
    return [RecordView.model_validate(record) for record in store.list_all()]


@records_router.post(
    "",
    response_model=RecordView,
    status_code=status.HTTP_201_CREATED,
    summary="Create a record",
    description="Mint an id, stamp the time server-side, persist, and return the record.",
)
def create_record(
    body: CreateRecordRequest,
    store: Annotated[RecordStore, Depends(get_store)],
    now: Annotated[str, Depends(get_now)],
) -> RecordView:
    """Build a record with a server-minted id and stamped time, persist, and project it."""
    record = Record(id=new_id(), name=body.name, created_at=now)
    store.add(record)
    return RecordView.model_validate(record)


@records_router.get(
    "/{record_id}",
    response_model=RecordView,
    summary="Fetch a record",
    description="Return the record with the given id, or a 404 rejection if absent.",
)
def get_record(
    record_id: str,
    store: Annotated[RecordStore, Depends(get_store)],
) -> RecordView:
    """Return one record by id (the app-level handler maps an absent id to 404)."""
    return RecordView.model_validate(store.get(record_id))
