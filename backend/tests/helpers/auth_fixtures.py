from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from tests.helpers.payloads import VALID_PASSWORD


@pytest_asyncio.fixture
async def make_user(user_factory, hasher):
    async def _create(password: str = VALID_PASSWORD, **kwargs: Any):
        hashed = await hasher.hash(password)
        return await user_factory(hashed_password=hashed, **kwargs)

    return _create


@pytest_asyncio.fixture
async def login_as(app, make_user):
    transport = ASGITransport(app=app)

    async def _login(user=None, password: str = VALID_PASSWORD, **kwargs):
        if user is None:
            user = await make_user(password=password, **kwargs)
        client = AsyncClient(transport=transport, base_url="http://testserver")
        resp = await client.post(
            "/api/v1/auth/login",
            json={"username": user.username, "password": password},
        )
        assert resp.status_code == 200, resp.text
        return client, user

    return _login


@pytest_asyncio.fixture
async def auth_client(login_as) -> AsyncIterator[tuple[AsyncClient, Any]]:
    client, user = await login_as()
    try:
        yield client, user
    finally:
        await client.aclose()


@pytest_asyncio.fixture
async def admin_client(login_as) -> AsyncIterator[tuple[AsyncClient, Any]]:
    client, user = await login_as(is_admin=True)
    try:
        yield client, user
    finally:
        await client.aclose()
