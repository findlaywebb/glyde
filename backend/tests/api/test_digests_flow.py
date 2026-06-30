"""End-to-end digests flow over the ASGITransport client (both store backings)."""

import httpx

_CODE_DIGEST = {
    "name": "PR",
    "text": "## H\n==big== news.\n\n```py\nx=1\n```",
    "source_kind": "cli",
}


async def test_create_then_fetch_round_trips(digest_client: httpx.AsyncClient) -> None:
    """A created digest is fetchable by slug, with a parsed block segment and stamped time."""
    created = await digest_client.post("/digests", json=_CODE_DIGEST)
    assert created.status_code == 201
    body = created.json()
    assert body["meta"]["created_at"] == "2025-01-01T00:00:00+00:00"  # frozen by conftest
    assert any(segment["type"] == "block" for segment in body["segments"])

    fetched = await digest_client.get(f"/digests/{body['meta']['slug']}")
    assert fetched.status_code == 200
    assert fetched.json() == body


async def test_list_returns_metadata_and_derived_counts(digest_client: httpx.AsyncClient) -> None:
    """The list route returns each digest's metadata plus derived shape counts."""
    await digest_client.post("/digests", json=_CODE_DIGEST)
    res = await digest_client.get("/digests")
    assert res.status_code == 200
    items = res.json()
    assert len(items) == 1
    assert items[0]["counts"]["words"] == 3
    assert items[0]["counts"]["blocks_by_kind"] == {"code": 1}


async def test_unknown_slug_is_a_404_rejection(digest_client: httpx.AsyncClient) -> None:
    """Fetching an absent slug yields the unknown_digest rejection with status 404."""
    res = await digest_client.get("/digests/no-such-slug")
    assert res.status_code == 404
    assert res.json()["code"] == "unknown_digest"


async def test_blank_name_is_rejected(digest_client: httpx.AsyncClient) -> None:
    """A blank name fails request validation (422) before the store is touched."""
    res = await digest_client.post(
        "/digests", json={"name": "", "text": "hi", "source_kind": "cli"}
    )
    assert res.status_code == 422


async def test_neither_text_nor_segments_is_rejected(digest_client: httpx.AsyncClient) -> None:
    """A request with neither text nor segments fails validation (exactly one required)."""
    res = await digest_client.post("/digests", json={"name": "x", "source_kind": "cli"})
    assert res.status_code == 422


async def test_create_from_pre_segmented_input(digest_client: httpx.AsyncClient) -> None:
    """A pre-segmented request (no text) builds and stores the supplied IR."""
    payload = {
        "name": "seg",
        "source_kind": "api",
        "segments": [
            {"type": "prose", "tokens": [{"text": "hello"}]},
            {"type": "pause", "reason": "sentence"},
        ],
    }
    created = await digest_client.post("/digests", json=payload)
    assert created.status_code == 201
    body = created.json()
    assert [segment["type"] for segment in body["segments"]] == ["prose", "pause"]
    assert body["meta"]["token_count"] == 1
