"""End-to-end preferences flow over the ASGITransport client (both store backings)."""

import httpx

from glyde.api.schemas import PreferencesView
from glyde.core import Preferences


def test_wire_view_defaults_match_the_core_defaults() -> None:
    """PreferencesView defaults equal core Preferences defaults (no silent drift)."""
    assert PreferencesView().model_dump() == Preferences().model_dump()


async def test_get_defaults_to_guided(digest_client: httpx.AsyncClient) -> None:
    """An owner with no stored preferences gets the guided defaults."""
    res = await digest_client.get("/preferences?owner_id=local")
    assert res.status_code == 200
    assert res.json()["mode"] == "guided"


async def test_put_partial_body_fills_defaults_and_persists(
    digest_client: httpx.AsyncClient,
) -> None:
    """A partial PUT validates (missing fields default) and the last-used mode persists."""
    put = await digest_client.put("/preferences", json={"owner_id": "local", "mode": "rsvp"})
    assert put.status_code == 200
    body = put.json()
    assert body["mode"] == "rsvp"
    assert body["wpm"] == 300  # missing field fell to its default

    got = await digest_client.get("/preferences?owner_id=local")
    assert got.json()["mode"] == "rsvp"


async def test_put_is_full_replace(digest_client: httpx.AsyncClient) -> None:
    """PUT replaces the whole row: a later partial PUT resets unspecified fields to defaults."""
    await digest_client.put("/preferences", json={"owner_id": "local", "mode": "rsvp", "wpm": 500})
    await digest_client.put("/preferences", json={"owner_id": "local", "mode": "fading"})
    got = await digest_client.get("/preferences?owner_id=local")
    assert got.json()["mode"] == "fading"
    assert got.json()["wpm"] == 300  # full-replace reset it to the default


async def test_put_rejects_unknown_field(digest_client: httpx.AsyncClient) -> None:
    """An unknown preferences field is rejected (extra=forbid -> 422)."""
    res = await digest_client.put("/preferences", json={"owner_id": "local", "bogus": 1})
    assert res.status_code == 422
