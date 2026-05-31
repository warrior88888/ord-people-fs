from __future__ import annotations

import pytest

from tests.helpers.payloads import above_max, below_min


class TestList:
    async def test_empty(self, client):
        r = await client.get("/api/v1/tags")
        assert r.status_code == 200
        assert r.json() == []

    async def test_with_tags(self, client, tag_factory):
        await tag_factory(name="alpha")
        await tag_factory(name="beta")
        r = await client.get("/api/v1/tags")
        names = {t["name"] for t in r.json()}
        assert names == {"alpha", "beta"}


class TestCreate:
    async def test_requires_auth(self, client):
        r = await client.post("/api/v1/tags", json={"name": "music"})
        assert r.status_code == 401

    async def test_requires_admin(self, auth_client):
        client, _ = auth_client
        r = await client.post("/api/v1/tags", json={"name": "music"})
        assert r.status_code == 403

    async def test_admin_happy(self, admin_client):
        client, _ = admin_client
        r = await client.post("/api/v1/tags", json={"name": "music"})
        assert r.status_code == 201
        assert r.json()["name"] == "music"

    async def test_duplicate_conflict(self, admin_client, tag_factory):
        await tag_factory(name="music")
        client, _ = admin_client
        r = await client.post("/api/v1/tags", json={"name": "music"})
        assert r.status_code == 409

    @pytest.mark.parametrize(
        "name", [below_min(2), above_max(64), 123, ""]
    )
    async def test_invalid(self, admin_client, name):
        client, _ = admin_client
        r = await client.post("/api/v1/tags", json={"name": name})
        assert r.status_code == 422

    async def test_missing_body(self, admin_client):
        client, _ = admin_client
        r = await client.post("/api/v1/tags", json={})
        assert r.status_code == 422
