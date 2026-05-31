from __future__ import annotations

import pytest

from tests.helpers.media import png_bytes
from tests.helpers.payloads import above_max, below_min


def _create_payload(**overrides):
    base = {
        "name": "Hello world",
        "description": "A nice description.",
        "category": "story",
        "external_url": None,
        "tag_ids": [],
    }
    base.update(overrides)
    if base["external_url"] is None:
        base.pop("external_url")
    return base


class TestFeed:
    async def test_empty(self, client):
        r = await client.get("/api/v1/posts")
        assert r.status_code == 200
        body = r.json()
        assert body == {"items": [], "total": 0, "limit": 20, "offset": 0}

    async def test_pagination(self, client, make_user, post_factory):
        u = await make_user()
        for _ in range(5):
            await post_factory(author_id=u.pk)
        r = await client.get("/api/v1/posts?limit=2&offset=0")
        body = r.json()
        assert body["total"] == 5
        assert len(body["items"]) == 2

    async def test_filter_by_category(self, client, make_user, post_factory):
        u = await make_user()
        await post_factory(author_id=u.pk, category="story")
        await post_factory(author_id=u.pk, category="event")
        r = await client.get("/api/v1/posts?category=event")
        items = r.json()["items"]
        assert len(items) == 1
        assert items[0]["category"] == "event"

    async def test_filter_by_tag_intersection(
        self, client, make_user, post_factory, tag_factory, db_session
    ):
        u = await make_user()
        t1 = await tag_factory(name="a-tag")
        t2 = await tag_factory(name="b-tag")
        p_both = await post_factory(author_id=u.pk, name="both")
        p_one = await post_factory(author_id=u.pk, name="one")
        from ord_people.models.tag import post_tags

        await db_session.execute(
            post_tags.insert(),
            [
                {"post_id": p_both.pk, "tag_id": t1.pk},
                {"post_id": p_both.pk, "tag_id": t2.pk},
                {"post_id": p_one.pk, "tag_id": t1.pk},
            ],
        )
        await db_session.commit()
        r = await client.get(f"/api/v1/posts?tag_ids={t1.pk}&tag_ids={t2.pk}")
        items = r.json()["items"]
        names = {i["name"] for i in items}
        assert names == {"both"}

    @pytest.mark.parametrize("limit", [0, 101])
    async def test_invalid_limit(self, client, limit):
        r = await client.get(f"/api/v1/posts?limit={limit}")
        assert r.status_code == 422

    async def test_invalid_category(self, client):
        r = await client.get("/api/v1/posts?category=nonexistent")
        assert r.status_code == 422


class TestCreate:
    async def test_requires_auth(self, client):
        r = await client.post("/api/v1/posts", json=_create_payload())
        assert r.status_code == 401

    async def test_happy(self, auth_client):
        client, _ = auth_client
        r = await client.post(
            "/api/v1/posts",
            json=_create_payload(name="Great post", description="A very good story."),
        )
        assert r.status_code == 201
        body = r.json()
        assert body["name"] == "Great post"
        assert body["author"]["pk"] > 0
        assert body["reactions"] == {"like": 0, "support": 0, "inspiring": 0}

    async def test_with_tags(self, auth_client, tag_factory):
        client, _ = auth_client
        t = await tag_factory()
        r = await client.post(
            "/api/v1/posts",
            json=_create_payload(tag_ids=[t.pk]),
        )
        assert r.status_code == 201
        tags = r.json()["tags"]
        assert len(tags) == 1
        assert tags[0]["pk"] == t.pk

    async def test_unknown_tag_ignored(self, auth_client):
        client, _ = auth_client
        r = await client.post(
            "/api/v1/posts",
            json=_create_payload(tag_ids=[999_999]),
        )
        assert r.status_code == 201
        assert r.json()["tags"] == []

    @pytest.mark.parametrize(
        ("field", "value"),
        [
            ("name", below_min(3)),
            ("name", above_max(50)),
            ("description", below_min(10)),
            ("description", above_max(1000)),
            ("category", "invalid_cat"),
            ("external_url", "not-a-url"),
        ],
    )
    async def test_invalid_inputs(self, auth_client, field, value):
        client, _ = auth_client
        r = await client.post(
            "/api/v1/posts", json=_create_payload(**{field: value})
        )
        assert r.status_code == 422

    async def test_empty_body(self, auth_client):
        client, _ = auth_client
        r = await client.post("/api/v1/posts", json={})
        assert r.status_code == 422


class TestGetOne:
    async def test_anonymous_can_read(self, client, post_factory):
        p = await post_factory()
        r = await client.get(f"/api/v1/posts/{p.pk}")
        assert r.status_code == 200
        assert r.json()["pk"] == p.pk
        assert r.json()["my_reaction"] is None

    async def test_404(self, client):
        r = await client.get("/api/v1/posts/999999")
        assert r.status_code == 404

    async def test_my_reaction_when_authenticated(
        self, login_as, make_user, post_factory, reaction_factory
    ):
        user = await make_user()
        post = await post_factory()
        await reaction_factory(post_id=post.pk, user_id=user.pk, reaction="like")
        client, _ = await login_as(user=user)
        r = await client.get(f"/api/v1/posts/{post.pk}")
        await client.aclose()
        assert r.status_code == 200
        assert r.json()["my_reaction"] == "like"


class TestUpdate:
    async def test_requires_auth(self, client, post_factory):
        p = await post_factory()
        r = await client.patch(f"/api/v1/posts/{p.pk}", json={"name": "x"})
        assert r.status_code == 401

    async def test_404(self, auth_client):
        client, _ = auth_client
        r = await client.patch("/api/v1/posts/999999", json={"name": "Hello"})
        assert r.status_code == 404

    async def test_non_owner_forbidden(self, auth_client, post_factory, user_factory):
        client, _ = auth_client
        other = await user_factory()
        post = await post_factory(author_id=other.pk)
        r = await client.patch(f"/api/v1/posts/{post.pk}", json={"name": "Hijack"})
        assert r.status_code == 403

    async def test_owner_update(self, login_as, make_user, post_factory):
        user = await make_user()
        post = await post_factory(author_id=user.pk)
        client, _ = await login_as(user=user)
        r = await client.patch(
            f"/api/v1/posts/{post.pk}",
            json={"name": "Renamed-by-owner"},
        )
        await client.aclose()
        assert r.status_code == 200
        assert r.json()["name"] == "Renamed-by-owner"

    async def test_partial_update(self, login_as, make_user, post_factory):
        user = await make_user()
        post = await post_factory(author_id=user.pk, name="orig")
        client, _ = await login_as(user=user)
        r = await client.patch(
            f"/api/v1/posts/{post.pk}",
            json={"description": "Updated description text."},
        )
        await client.aclose()
        assert r.status_code == 200
        body = r.json()
        assert body["name"] == "orig"
        assert body["description"] == "Updated description text."

    @pytest.mark.parametrize(
        ("field", "value"),
        [
            ("name", above_max(50)),
            ("description", below_min(10)),
            ("category", "garbage"),
        ],
    )
    async def test_invalid(self, login_as, make_user, post_factory, field, value):
        user = await make_user()
        post = await post_factory(author_id=user.pk)
        client, _ = await login_as(user=user)
        r = await client.patch(f"/api/v1/posts/{post.pk}", json={field: value})
        await client.aclose()
        assert r.status_code == 422


class TestDelete:
    async def test_requires_auth(self, client, post_factory):
        p = await post_factory()
        r = await client.delete(f"/api/v1/posts/{p.pk}")
        assert r.status_code == 401

    async def test_404(self, auth_client):
        client, _ = auth_client
        r = await client.delete("/api/v1/posts/999999")
        assert r.status_code == 404

    async def test_non_owner_forbidden(self, auth_client, post_factory, user_factory):
        client, _ = auth_client
        other = await user_factory()
        post = await post_factory(author_id=other.pk)
        r = await client.delete(f"/api/v1/posts/{post.pk}")
        assert r.status_code == 403

    async def test_owner_delete(self, login_as, make_user, post_factory):
        user = await make_user()
        post = await post_factory(author_id=user.pk)
        client, _ = await login_as(user=user)
        r = await client.delete(f"/api/v1/posts/{post.pk}")
        await client.aclose()
        assert r.status_code == 204

    async def test_admin_can_delete(self, login_as, post_factory, user_factory):
        owner = await user_factory()
        post = await post_factory(author_id=owner.pk)
        admin_client_, _ = await login_as(is_admin=True)
        r = await admin_client_.delete(f"/api/v1/posts/{post.pk}")
        await admin_client_.aclose()
        assert r.status_code == 204

    async def test_cascade_comments(
        self, login_as, make_user, post_factory, comment_factory, db_session
    ):
        user = await make_user()
        post = await post_factory(author_id=user.pk)
        comment = await comment_factory(post_id=post.pk, author_id=user.pk)
        client, _ = await login_as(user=user)
        await client.delete(f"/api/v1/posts/{post.pk}")
        await client.aclose()
        from ord_people.models.comment import Comment

        assert await db_session.get(Comment, comment.pk) is None


class TestPhotoUpload:
    async def test_requires_auth(self, client, post_factory):
        p = await post_factory()
        r = await client.post(
            f"/api/v1/posts/{p.pk}/photo",
            files={"file": ("a.png", png_bytes(), "image/png")},
        )
        assert r.status_code == 401

    async def test_non_owner_forbidden(self, auth_client, post_factory, user_factory):
        client, _ = auth_client
        other = await user_factory()
        post = await post_factory(author_id=other.pk)
        r = await client.post(
            f"/api/v1/posts/{post.pk}/photo",
            files={"file": ("a.png", png_bytes(), "image/png")},
        )
        assert r.status_code == 403

    async def test_owner_happy(self, login_as, make_user, post_factory, app):
        user = await make_user()
        post = await post_factory(author_id=user.pk)
        client, _ = await login_as(user=user)
        r = await client.post(
            f"/api/v1/posts/{post.pk}/photo",
            files={"file": ("a.png", png_bytes(), "image/png")},
        )
        await client.aclose()
        assert r.status_code == 200
        assert r.json()["photo_url"].startswith("https://fake.cdn/")
        assert len(app.state.storage.objects) >= 1

    async def test_post_404(self, auth_client):
        client, _ = auth_client
        r = await client.post(
            "/api/v1/posts/999999/photo",
            files={"file": ("a.png", png_bytes(), "image/png")},
        )
        assert r.status_code == 404


class TestPhotoDelete:
    async def test_requires_auth(self, client, post_factory):
        p = await post_factory()
        r = await client.delete(f"/api/v1/posts/{p.pk}/photo")
        assert r.status_code == 401

    async def test_non_owner_forbidden(self, auth_client, post_factory, user_factory):
        client, _ = auth_client
        other = await user_factory()
        post = await post_factory(author_id=other.pk)
        r = await client.delete(f"/api/v1/posts/{post.pk}/photo")
        assert r.status_code == 403

    async def test_post_404(self, auth_client):
        client, _ = auth_client
        r = await client.delete("/api/v1/posts/999999/photo")
        assert r.status_code == 404

    async def test_owner_removes_photo(
        self, login_as, make_user, post_factory, app, db_session
    ):
        user = await make_user()
        post = await post_factory(author_id=user.pk)
        client, _ = await login_as(user=user)
        await client.post(
            f"/api/v1/posts/{post.pk}/photo",
            files={"file": ("a.png", png_bytes(), "image/png")},
        )
        deletes_before = len(app.state.storage.deletes)
        r = await client.delete(f"/api/v1/posts/{post.pk}/photo")
        await client.aclose()
        assert r.status_code == 204
        assert len(app.state.storage.deletes) == deletes_before + 1
        from ord_people.models.post import Post

        fresh = await db_session.get(Post, post.pk)
        await db_session.refresh(fresh)
        assert fresh.photo_key is None

    async def test_idempotent_when_no_photo(self, login_as, make_user, post_factory, app):
        user = await make_user()
        post = await post_factory(author_id=user.pk)
        client, _ = await login_as(user=user)
        deletes_before = len(app.state.storage.deletes)
        r = await client.delete(f"/api/v1/posts/{post.pk}/photo")
        await client.aclose()
        assert r.status_code == 204
        assert len(app.state.storage.deletes) == deletes_before
