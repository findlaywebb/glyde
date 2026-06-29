"""End-to-end records flow over the ASGITransport client (both store backings)."""

import httpx


async def test_create_then_fetch_round_trips(client: httpx.AsyncClient) -> None:
    """A created record is returned by its id with a server-stamped time."""
    created = await client.post("/records", json={"name": "first"})
    assert created.status_code == 201
    body = created.json()
    assert body["name"] == "first"
    assert body["created_at"] == "2025-01-01T00:00:00+00:00"  # frozen by conftest

    fetched = await client.get(f"/records/{body['id']}")
    assert fetched.status_code == 200
    assert fetched.json() == body


async def test_unknown_record_is_a_404_rejection(client: httpx.AsyncClient) -> None:
    """Fetching an absent id yields the {code, message} rejection body with status 404."""
    res = await client.get("/records/does-not-exist")
    assert res.status_code == 404
    assert res.json()["code"] == "unknown_record"


async def test_blank_name_is_rejected(client: httpx.AsyncClient) -> None:
    """A blank name fails request validation (422) before the store is touched."""
    res = await client.post("/records", json={"name": ""})
    assert res.status_code == 422


async def test_list_returns_created_records(client: httpx.AsyncClient) -> None:
    """List returns the records created in this session."""
    await client.post("/records", json={"name": "a"})
    await client.post("/records", json={"name": "b"})
    res = await client.get("/records")
    assert res.status_code == 200
    assert {r["name"] for r in res.json()} == {"a", "b"}
