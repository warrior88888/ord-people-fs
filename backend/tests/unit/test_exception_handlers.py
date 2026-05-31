from __future__ import annotations

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from httpx import ASGITransport, AsyncClient

from ord_people.exception_handlers import register_exception_handlers
from ord_people.exceptions import (
    AppError,
    NotFoundError,
    UnauthorizedError,
    UsernameAlreadyTakenError,
)


def _build_app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/raise-app")
    async def raise_app():
        raise UsernameAlreadyTakenError

    @app.get("/raise-not-found")
    async def raise_nf():
        raise NotFoundError

    @app.get("/raise-unauth")
    async def raise_unauth():
        raise UnauthorizedError

    @app.get("/raise-generic")
    async def raise_app2():
        raise AppError

    @app.get("/raise-validation")
    async def raise_validation():
        raise RequestValidationError(errors=[])

    @app.get("/raise-unhandled")
    async def raise_unhandled():
        raise RuntimeError("boom")

    return app


async def test_app_error_returns_status_and_detail():
    transport = ASGITransport(app=_build_app(), raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://t") as c:
        r = await c.get("/raise-app")
        assert r.status_code == 409
        assert r.json()["detail"] == "Username already taken"


async def test_not_found_handler():
    transport = ASGITransport(app=_build_app(), raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://t") as c:
        r = await c.get("/raise-not-found")
        assert r.status_code == 404


async def test_unauthorized_handler():
    transport = ASGITransport(app=_build_app(), raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://t") as c:
        r = await c.get("/raise-unauth")
        assert r.status_code == 401


async def test_generic_app_error():
    transport = ASGITransport(app=_build_app(), raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://t") as c:
        r = await c.get("/raise-generic")
        assert r.status_code == 500


async def test_validation_handler():
    transport = ASGITransport(app=_build_app(), raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://t") as c:
        r = await c.get("/raise-validation")
        assert r.status_code == 422


async def test_unhandled_returns_500():
    transport = ASGITransport(app=_build_app(), raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://t") as c:
        r = await c.get("/raise-unhandled")
        assert r.status_code == 500
        assert r.json() == {"detail": "Internal error"}
