from __future__ import annotations

import pytest


class TestToggle:
    async def test_requires_auth(self, client, post_factory):
        p = await post_factory()
        r = await client.post(
            f"/api/v1/posts/{p.pk}/reactions", json={"reaction": "like"}
        )
        assert r.status_code == 401

    async def test_post_404(self, auth_client):
        client, _ = auth_client
        r = await client.post(
            "/api/v1/posts/999999/reactions", json={"reaction": "like"}
        )
        assert r.status_code == 404

    @pytest.mark.parametrize("bad", ["nope", "LIKE_caps", "", 42])
    async def test_invalid_reaction(self, auth_client, post_factory, bad):
        client, _ = auth_client
        p = await post_factory()
        r = await client.post(
            f"/api/v1/posts/{p.pk}/reactions", json={"reaction": bad}
        )
        assert r.status_code == 422

    async def test_add_reaction(self, auth_client, post_factory):
        client, _ = auth_client
        p = await post_factory()
        r = await client.post(
            f"/api/v1/posts/{p.pk}/reactions", json={"reaction": "like"}
        )
        assert r.status_code == 200
        body = r.json()
        assert body["counts"]["like"] == 1
        assert body["my_reaction"] == "like"

    async def test_replace_reaction(self, auth_client, post_factory):
        client, _ = auth_client
        p = await post_factory()
        await client.post(
            f"/api/v1/posts/{p.pk}/reactions", json={"reaction": "like"}
        )
        r = await client.post(
            f"/api/v1/posts/{p.pk}/reactions", json={"reaction": "support"}
        )
        body = r.json()
        assert body["counts"]["like"] == 0
        assert body["counts"]["support"] == 1
        assert body["my_reaction"] == "support"

    async def test_toggle_off(self, auth_client, post_factory):
        client, _ = auth_client
        p = await post_factory()
        await client.post(
            f"/api/v1/posts/{p.pk}/reactions", json={"reaction": "like"}
        )
        r = await client.post(
            f"/api/v1/posts/{p.pk}/reactions", json={"reaction": "like"}
        )
        body = r.json()
        assert body["counts"]["like"] == 0
        assert body["my_reaction"] is None

    async def test_multi_user_aggregation(
        self, login_as, make_user, post_factory
    ):
        post = await post_factory()
        for _ in range(3):
            user = await make_user()
            c, _ = await login_as(user=user)
            await c.post(
                f"/api/v1/posts/{post.pk}/reactions", json={"reaction": "like"}
            )
            await c.aclose()
        for _ in range(2):
            user = await make_user()
            c, _ = await login_as(user=user)
            await c.post(
                f"/api/v1/posts/{post.pk}/reactions", json={"reaction": "support"}
            )
            await c.aclose()
        # any client to read
        final_user = await make_user()
        final, _ = await login_as(user=final_user)
        r = await final.post(
            f"/api/v1/posts/{post.pk}/reactions", json={"reaction": "inspiring"}
        )
        await final.aclose()
        body = r.json()
        assert body["counts"]["like"] == 3
        assert body["counts"]["support"] == 2
        assert body["counts"]["inspiring"] == 1
