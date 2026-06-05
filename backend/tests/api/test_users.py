from __future__ import annotations

import pytest

from tests.helpers.media import heic_bytes, jpeg_bytes, oversized_bytes, png_bytes
from tests.helpers.payloads import VALID_PASSWORD, above_max, below_min


class TestListFeed:
    async def test_empty(self, client):
        r = await client.get("/api/v1/users")
        assert r.status_code == 200
        body = r.json()
        assert body["items"] == []
        assert body["total"] == 0
        assert body["limit"] == 20
        assert body["offset"] == 0

    async def test_with_users(self, client, make_user):
        for _ in range(3):
            await make_user()
        r = await client.get("/api/v1/users?limit=2&offset=0")
        assert r.status_code == 200
        body = r.json()
        assert len(body["items"]) == 2
        assert body["total"] == 3

    async def test_inactive_user_excluded(self, client, make_user):
        await make_user(is_active=False)
        r = await client.get("/api/v1/users")
        assert r.status_code == 200
        assert r.json()["total"] == 0

    @pytest.mark.parametrize("limit", [0, -1, 101, 500])
    async def test_invalid_limit(self, client, limit):
        r = await client.get(f"/api/v1/users?limit={limit}")
        assert r.status_code == 422

    @pytest.mark.parametrize("offset", [-1, -100])
    async def test_invalid_offset(self, client, offset):
        r = await client.get(f"/api/v1/users?offset={offset}")
        assert r.status_code == 422


class TestGetMe:
    async def test_requires_auth(self, client):
        r = await client.get("/api/v1/users/me")
        assert r.status_code == 401

    async def test_happy(self, auth_client):
        client, user = auth_client
        r = await client.get("/api/v1/users/me")
        assert r.status_code == 200
        body = r.json()
        assert body["username"] == user.username
        assert body["pk"] == user.pk
        assert body["bio"] is None

    async def test_includes_bio(self, login_as, make_user, bio_factory):
        user = await make_user(username="biouser")
        await bio_factory(user_id=user.pk, about="hello world")
        client, _ = await login_as(user=user)
        r = await client.get("/api/v1/users/me")
        await client.aclose()
        assert r.status_code == 200
        assert r.json()["bio"]["about"] == "hello world"


class TestPatchMe:
    async def test_requires_auth(self, client):
        r = await client.patch("/api/v1/users/me", json={"first_name": "X"})
        assert r.status_code == 401

    async def test_update_fields(self, auth_client):
        client, _ = auth_client
        r = await client.patch(
            "/api/v1/users/me",
            json={"first_name": "Alice", "last_name": "Wonder"},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["first_name"] == "Alice"
        assert body["last_name"] == "Wonder"

    async def test_partial_update(self, auth_client):
        client, _ = auth_client
        r = await client.patch("/api/v1/users/me", json={"first_name": "Solo"})
        assert r.status_code == 200
        assert r.json()["first_name"] == "Solo"

    async def test_empty_body_is_noop(self, auth_client):
        client, user = auth_client
        r = await client.patch("/api/v1/users/me", json={})
        assert r.status_code == 200
        assert r.json()["username"] == user.username

    @pytest.mark.parametrize(
        ("field", "value"),
        [
            ("first_name", below_min(2)),
            ("first_name", above_max(32)),
            ("last_name", below_min(2)),
            ("last_name", above_max(32)),
            ("first_name", 123),
        ],
    )
    async def test_invalid(self, auth_client, field, value):
        client, _ = auth_client
        r = await client.patch("/api/v1/users/me", json={field: value})
        assert r.status_code == 422


class TestDeleteMe:
    async def test_requires_auth(self, client):
        r = await client.delete("/api/v1/users/me")
        assert r.status_code == 401

    async def test_happy(self, auth_client):
        client, _user = auth_client
        r = await client.delete("/api/v1/users/me")
        assert r.status_code == 204
        me = await client.get("/api/v1/users/me")
        assert me.status_code == 401

    async def test_anonymizes_user(self, login_as, make_user, db_session):
        user = await make_user(username="todelete")
        client, _ = await login_as(user=user)
        r = await client.delete("/api/v1/users/me")
        await client.aclose()
        assert r.status_code == 204
        from ord_people.models.user import User

        await db_session.refresh(await db_session.get(User, user.pk))
        fresh = await db_session.get(User, user.pk)
        assert fresh.is_active is False
        assert fresh.username.startswith("deleted-")
        assert fresh.deleted_at is not None


class TestUpdateBio:
    async def test_requires_auth(self, client):
        r = await client.put("/api/v1/users/me/bio", json={"about": "hi"})
        assert r.status_code == 401

    async def test_happy(self, auth_client):
        client, _ = auth_client
        r = await client.put(
            "/api/v1/users/me/bio",
            json={
                "about": "Hello there",
                "phone_number": "+71234567890",
                "vk_link": "https://vk.com/alice",
            },
        )
        assert r.status_code == 200
        body = r.json()
        assert body["about"] == "Hello there"
        assert body["phone_number"] == "+71234567890"

    @pytest.mark.parametrize(
        ("field", "value"),
        [
            ("phone_number", "123"),
            ("phone_number", "+10000000000"),
            ("vk_link", "https://evil.com/x"),
            ("max_link", "https://yandex.ru/"),
            ("email", "not-an-email"),
            ("about", "x" * 2001),
        ],
    )
    async def test_invalid(self, auth_client, field, value):
        client, _ = auth_client
        r = await client.put("/api/v1/users/me/bio", json={field: value})
        assert r.status_code == 422

    async def test_clear_phone_with_empty_string(self, auth_client):
        client, _ = auth_client
        r = await client.put(
            "/api/v1/users/me/bio",
            json={"phone_number": ""},
        )
        assert r.status_code == 200
        assert r.json()["phone_number"] is None


class TestAvatarUpload:
    async def test_requires_auth(self, client):
        r = await client.put(
            "/api/v1/users/me/avatar",
            files={"file": ("a.png", png_bytes(), "image/png")},
        )
        assert r.status_code == 401

    async def test_happy_png(self, auth_client, app):
        client, _ = auth_client
        r = await client.put(
            "/api/v1/users/me/avatar",
            files={"file": ("a.png", png_bytes(), "image/png")},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["avatar_url"].startswith("https://fake.cdn/")
        assert len(app.state.storage.objects) == 1

    async def test_happy_jpeg(self, auth_client):
        client, _ = auth_client
        r = await client.put(
            "/api/v1/users/me/avatar",
            files={"file": ("a.jpg", jpeg_bytes(), "image/jpeg")},
        )
        assert r.status_code == 200

    async def test_happy_heic_from_iphone(self, auth_client, app):
        client, _ = auth_client
        r = await client.put(
            "/api/v1/users/me/avatar",
            files={"file": ("IMG_1234.HEIC", heic_bytes(), "image/heic")},
        )
        assert r.status_code == 200
        assert len(app.state.storage.objects) == 1

    async def test_oversized_rejected(self, auth_client):
        client, _ = auth_client
        r = await client.put(
            "/api/v1/users/me/avatar",
            files={"file": ("big.png", oversized_bytes(), "image/png")},
        )
        assert r.status_code == 400

    async def test_replaces_old(self, auth_client, app):
        client, _ = auth_client
        await client.put(
            "/api/v1/users/me/avatar",
            files={"file": ("a.png", png_bytes(), "image/png")},
        )
        await client.put(
            "/api/v1/users/me/avatar",
            files={"file": ("b.png", png_bytes(), "image/png")},
        )
        assert len(app.state.storage.deletes) >= 1

    async def test_missing_file(self, auth_client):
        client, _ = auth_client
        r = await client.put("/api/v1/users/me/avatar")
        assert r.status_code == 422

    async def test_non_image_content_type_rejected(self, auth_client):
        client, _ = auth_client
        r = await client.put(
            "/api/v1/users/me/avatar",
            files={"file": ("a.txt", b"hello world", "text/plain")},
        )
        assert r.status_code == 415


class TestAvatarDelete:
    async def test_requires_auth(self, client):
        r = await client.delete("/api/v1/users/me/avatar")
        assert r.status_code == 401

    async def test_removes_existing_avatar(self, auth_client, app, db_session):
        client, user = auth_client
        await client.put(
            "/api/v1/users/me/avatar",
            files={"file": ("a.png", png_bytes(), "image/png")},
        )
        deletes_before = len(app.state.storage.deletes)
        r = await client.delete("/api/v1/users/me/avatar")
        assert r.status_code == 204
        assert len(app.state.storage.deletes) == deletes_before + 1
        from ord_people.models.user import User

        fresh = await db_session.get(User, user.pk)
        await db_session.refresh(fresh)
        assert fresh.avatar_key is None

    async def test_idempotent_when_no_avatar(self, auth_client, app):
        client, _ = auth_client
        deletes_before = len(app.state.storage.deletes)
        r = await client.delete("/api/v1/users/me/avatar")
        assert r.status_code == 204
        assert len(app.state.storage.deletes) == deletes_before



class TestGetByUsername:
    async def test_404(self, client):
        r = await client.get("/api/v1/users/nobody")
        assert r.status_code == 404

    async def test_happy(self, client, make_user):
        u = await make_user(username="targetx")
        r = await client.get(f"/api/v1/users/{u.username}")
        assert r.status_code == 200
        assert r.json()["username"] == "targetx"

    async def test_deleted_user_returns_404(self, client, make_user, login_as):
        user = await make_user(username="todelete2", password=VALID_PASSWORD)
        c, _ = await login_as(user=user)
        await c.delete("/api/v1/users/me")
        await c.aclose()
        r = await client.get("/api/v1/users/todelete2")
        assert r.status_code == 404


class TestGetUserPosts:
    async def test_404_user(self, client):
        r = await client.get("/api/v1/users/ghosty/posts")
        assert r.status_code == 404

    async def test_returns_only_owned(self, client, make_user, post_factory):
        u1 = await make_user(username="poster1")
        u2 = await make_user(username="poster2")
        await post_factory(author_id=u1.pk, name="P1")
        await post_factory(author_id=u2.pk, name="P2")
        r = await client.get(f"/api/v1/users/{u1.username}/posts")
        assert r.status_code == 200
        items = r.json()["items"]
        assert len(items) == 1
        assert items[0]["name"] == "P1"

    async def test_pagination(self, client, make_user, post_factory):
        u = await make_user(username="postery")
        for _ in range(5):
            await post_factory(author_id=u.pk)
        r = await client.get(f"/api/v1/users/{u.username}/posts?limit=2&offset=0")
        assert r.status_code == 200
        body = r.json()
        assert len(body["items"]) == 2
        assert body["total"] == 5
