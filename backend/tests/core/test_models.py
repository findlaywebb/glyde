"""Tests for the example ``Record`` domain model."""

import pytest
from pydantic import ValidationError

from glyde.core import Record


def test_record_round_trips_through_validation() -> None:
    """A Record built from valid fields keeps them verbatim."""
    rec = Record(id="a", name="example", created_at="2025-01-01T00:00:00+00:00")
    assert (rec.id, rec.name, rec.created_at) == ("a", "example", "2025-01-01T00:00:00+00:00")


def test_record_rejects_blank_name() -> None:
    """A blank name fails validation — names are non-blank by contract."""
    with pytest.raises(ValidationError):
        Record(id="a", name="", created_at="2025-01-01T00:00:00+00:00")


def test_record_is_frozen() -> None:
    """A Record is immutable once built."""
    rec = Record(id="a", name="example", created_at="2025-01-01T00:00:00+00:00")
    with pytest.raises(ValidationError):
        rec.name = "changed"
