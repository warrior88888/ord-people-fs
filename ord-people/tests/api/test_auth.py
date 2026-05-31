from __future__ import annotations

import pytest

from tests.helpers.payloads import VALID_PASSWORD


def _register_payload(**overrides):
    base = {
        "username": "alice-42",
        "password": VALID_PASSWORD,
        "first_name": "Alice",
        "last_name": "Smith",
    }
    base.update(overrides)
    return base


class TestRegister:
    async def test_happy_path(self, client):
        resp = await client.post("/api/v1/auth/register", json=_register_payload())
        assert resp.status_code == 201
        body = resp.json()
        assert body["username"] == "alice-42"
        assert body["user_id"] > 0
        assert resp.cookies.get("session_id")

    async def test_username_taken(self, client, make_user):
        await make_user(username="alice-42")
        resp = await client.post("/api/v1/auth/register", json=_register_payload())
        assert resp.status_code == 409

    @pytest.mark.parametrize(
        ("field", "value"),
        [
            ("username", ""),
            ("username", "a"),
            ("username", "x" * 100),
            ("username", "has space"),
            ("username", "1startswithdigit"),
            ("username", "has__double_underscore"),
            ("password", "short"),
            ("first_name", ""),
            ("first_name", "a"),
            ("last_name", ""),
            ("password", "x" * 200),
        ],
    )
    async def test_invalid_inputs(self, client, field, value):
        resp = await client.post(
            "/api/v1/auth/register", json=_register_payload(**{field: value})
        )
        assert resp.status_code == 422

    async def test_empty_body(self, client):
        resp = await client.post("/api/v1/auth/register", json={})
        assert resp.status_code == 422

    async def test_missing_field(self, client):
        payload = _register_payload()
        del payload["password"]
        resp = await client.post("/api/v1/auth/register", json=payload)
        assert resp.status_code == 422

    async def test_wrong_content_type(self, client):
        resp = await client.post(
            "/api/v1/auth/register",
            content="username=x&password=x",
            headers={"content-type": "application/x-www-form-urlencoded"},
        )
        assert resp.status_code == 422

    async def test_wrong_type(self, client):
        resp = await client.post(
            "/api/v1/auth/register",
            json=_register_payload(password=12345678),
        )
        assert resp.status_code == 422


class TestLogin:
    async def test_happy_path(self, client, make_user):
        await make_user(username="bobby", password=VALID_PASSWORD)
        resp = await client.post(
            "/api/v1/auth/login",
            json={"username": "bobby", "password": VALID_PASSWORD},
        )
        assert resp.status_code == 200
        assert resp.cookies.get("session_id")

    async def test_unknown_user(self, client):
        resp = await client.post(
            "/api/v1/auth/login",
            json={"username": "ghosty", "password": VALID_PASSWORD},
        )
        assert resp.status_code == 401

    async def test_wrong_password(self, client, make_user):
        await make_user(username="bobby", password=VALID_PASSWORD)
        resp = await client.post(
            "/api/v1/auth/login",
            json={"username": "bobby", "password": "WrongPassword1!"},
        )
        assert resp.status_code == 401

    async def test_inactive_user_blocked(self, client, make_user):
        await make_user(username="bobby", password=VALID_PASSWORD, is_active=False)
        resp = await client.post(
            "/api/v1/auth/login",
            json={"username": "bobby", "password": VALID_PASSWORD},
        )
        assert resp.status_code == 401

    async def test_invalid_username(self, client):
        resp = await client.post(
            "/api/v1/auth/login",
            json={"username": "a b", "password": VALID_PASSWORD},
        )
        assert resp.status_code == 422

    async def test_missing_body(self, client):
        resp = await client.post("/api/v1/auth/login", json={})
        assert resp.status_code == 422


class TestLogout:
    async def test_logout_clears_session(self, auth_client):
        client, _ = auth_client
        resp = await client.post("/api/v1/auth/logout")
        assert resp.status_code == 200
        me = await client.get("/api/v1/users/me")
        assert me.status_code == 401

    async def test_logout_without_cookie_is_ok(self, client):
        resp = await client.post("/api/v1/auth/logout")
        assert resp.status_code == 200

    async def test_logout_all_requires_auth(self, client):
        resp = await client.post("/api/v1/auth/logout-all")
        assert resp.status_code == 401

    async def test_logout_all_kills_other_sessions(self, login_as, make_user):
        user = await make_user(username="kevvy")
        client_a, _ = await login_as(user=user)
        client_b, _ = await login_as(user=user)
        resp = await client_a.post("/api/v1/auth/logout-all")
        assert resp.status_code == 200
        me_b = await client_b.get("/api/v1/users/me")
        assert me_b.status_code == 401
        await client_a.aclose()
        await client_b.aclose()


class TestSessionTampering:
    async def test_invalid_cookie_signature(self, client):
        client.cookies.set("session_id", "totally-fake")
        me = await client.get("/api/v1/users/me")
        assert me.status_code == 401

    async def test_garbage_cookie(self, client):
        client.cookies.set("session_id", "x.y.z.signed.maybe")
        me = await client.get("/api/v1/users/me")
        assert me.status_code == 401
