from __future__ import annotations

import pytest

from tests.helpers.payloads import above_max, below_min


class TestList:
    async def test_post_not_found(self, client):
        r = await client.get("/api/v1/posts/999999/comments")
        assert r.status_code == 404

    async def test_empty(self, client, post_factory):
        p = await post_factory()
        r = await client.get(f"/api/v1/posts/{p.pk}/comments")
        assert r.status_code == 200
        assert r.json()["items"] == []

    async def test_pagination(self, client, post_factory, comment_factory):
        p = await post_factory()
        for _ in range(5):
            await comment_factory(post_id=p.pk)
        r = await client.get(f"/api/v1/posts/{p.pk}/comments?limit=2&offset=0")
        body = r.json()
        assert len(body["items"]) == 2
        assert body["total"] == 5


class TestCreate:
    async def test_requires_auth(self, client, post_factory):
        p = await post_factory()
        r = await client.post(
            f"/api/v1/posts/{p.pk}/comments", json={"text": "hello there"}
        )
        assert r.status_code == 401

    async def test_post_404(self, auth_client):
        client, _ = auth_client
        r = await client.post(
            "/api/v1/posts/999999/comments", json={"text": "hello there"}
        )
        assert r.status_code == 404

    async def test_happy(self, auth_client, post_factory):
        client, _ = auth_client
        p = await post_factory()
        r = await client.post(
            f"/api/v1/posts/{p.pk}/comments", json={"text": "first comment"}
        )
        assert r.status_code == 201
        body = r.json()
        assert body["text"] == "first comment"
        assert body["author"]["pk"] > 0

    @pytest.mark.parametrize(
        "text",
        [
            below_min(2),
            above_max(100),
        ],
    )
    async def test_invalid_text(self, auth_client, post_factory, text):
        client, _ = auth_client
        p = await post_factory()
        r = await client.post(
            f"/api/v1/posts/{p.pk}/comments", json={"text": text}
        )
        assert r.status_code == 422

    async def test_missing_text(self, auth_client, post_factory):
        client, _ = auth_client
        p = await post_factory()
        r = await client.post(f"/api/v1/posts/{p.pk}/comments", json={})
        assert r.status_code == 422


class TestUpdate:
    async def test_requires_auth(self, client, comment_factory):
        c = await comment_factory()
        r = await client.patch(
            f"/api/v1/posts/{c.post_id}/comments/{c.pk}", json={"text": "new"}
        )
        assert r.status_code == 401

    async def test_404(self, auth_client):
        client, _ = auth_client
        r = await client.patch(
            "/api/v1/posts/1/comments/999999", json={"text": "new text"}
        )
        assert r.status_code == 404

    async def test_post_mismatch_404(self, auth_client, comment_factory, post_factory):
        client, _ = auth_client
        c = await comment_factory()
        other = await post_factory()
        r = await client.patch(
            f"/api/v1/posts/{other.pk}/comments/{c.pk}", json={"text": "new text"}
        )
        assert r.status_code == 404

    async def test_non_owner_forbidden(self, auth_client, comment_factory):
        client, _ = auth_client
        c = await comment_factory()
        r = await client.patch(
            f"/api/v1/posts/{c.post_id}/comments/{c.pk}", json={"text": "new text"}
        )
        assert r.status_code == 403

    async def test_owner_update(self, login_as, make_user, post_factory, comment_factory):
        user = await make_user()
        post = await post_factory()
        c = await comment_factory(post_id=post.pk, author_id=user.pk)
        client, _ = await login_as(user=user)
        r = await client.patch(
            f"/api/v1/posts/{post.pk}/comments/{c.pk}",
            json={"text": "updated comment"},
        )
        await client.aclose()
        assert r.status_code == 200
        assert r.json()["text"] == "updated comment"


class TestDelete:
    async def test_requires_auth(self, client, comment_factory):
        c = await comment_factory()
        r = await client.delete(f"/api/v1/posts/{c.post_id}/comments/{c.pk}")
        assert r.status_code == 401

    async def test_404(self, auth_client):
        client, _ = auth_client
        r = await client.delete("/api/v1/posts/1/comments/999999")
        assert r.status_code == 404

    async def test_non_owner_forbidden(self, auth_client, comment_factory):
        client, _ = auth_client
        c = await comment_factory()
        r = await client.delete(f"/api/v1/posts/{c.post_id}/comments/{c.pk}")
        assert r.status_code == 403

    async def test_owner_delete(self, login_as, make_user, comment_factory, post_factory):
        user = await make_user()
        post = await post_factory()
        c = await comment_factory(post_id=post.pk, author_id=user.pk)
        client, _ = await login_as(user=user)
        r = await client.delete(f"/api/v1/posts/{post.pk}/comments/{c.pk}")
        await client.aclose()
        assert r.status_code == 204

    async def test_admin_can_delete(self, login_as, comment_factory):
        c = await comment_factory()
        admin_, _ = await login_as(is_admin=True)
        r = await admin_.delete(f"/api/v1/posts/{c.post_id}/comments/{c.pk}")
        await admin_.aclose()
        assert r.status_code == 204
