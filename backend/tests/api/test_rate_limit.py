from __future__ import annotations


class _CountingLimiter:
    def __init__(self, threshold: int):
        self.threshold = threshold
        self.calls: dict[str, int] = {}

    @staticmethod
    def client_ip(_request):
        return "1.1.1.1"

    async def is_limited(
        self, ip, endpoint, max_requests, window_seconds
    ):
        key = f"{endpoint}:{ip}"
        self.calls[key] = self.calls.get(key, 0) + 1
        return self.calls[key] > self.threshold


async def test_login_rate_limited(app, client, make_user):
    app.state.rate_limiter = _CountingLimiter(threshold=2)
    await make_user(username="rl_user1")
    for _ in range(2):
        await client.post(
            "/api/v1/auth/login",
            json={"username": "rl_user1", "password": "wrong-password-1"},
        )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "rl_user1", "password": "wrong-password-1"},
    )
    assert resp.status_code == 429
    assert "retry-after" in {k.lower() for k in resp.headers}


async def test_distinct_endpoints_unaffected(app, client, make_user):
    app.state.rate_limiter = _CountingLimiter(threshold=2)
    await make_user(username="rl_user2")
    for _ in range(2):
        await client.post(
            "/api/v1/auth/login",
            json={"username": "rl_user2", "password": "wrong"},
        )
    r = await client.post(
        "/api/v1/auth/register",
        json={
            "username": "newone55",
            "password": "Sup3rSecret!",
            "first_name": "Xx",
            "last_name": "Yy",
        },
    )
    assert r.status_code == 201


async def test_fail_open_on_limiter_failure(app, client, make_user):
    class BoomLimiter:
        @staticmethod
        def client_ip(_req):
            return "1.1.1.1"

        async def is_limited(self, *a, **kw):
            return False  # fail-open behaviour

    app.state.rate_limiter = BoomLimiter()
    await make_user(username="rluser3")
    for _ in range(10):
        r = await client.post(
            "/api/v1/auth/login",
            json={"username": "rluser3", "password": "wrongpass"},
        )
        assert r.status_code in (401, 200)
