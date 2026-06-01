from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import pytest
import pytest_asyncio
import redis.asyncio as redis
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from ord_people.api import api_router
from ord_people.exceptions import AppError
from ord_people.infra.auth.password_hasher import Argon2PasswordHasher
from ord_people.infra.auth.session_repository import RedisSessionRepository
from ord_people.infra.auth.session_signer import ItsDangerousSessionSigner
from ord_people.infra.cache.redis import RedisCache
from ord_people.infra.rate_limit import RateLimiter
from ord_people.models import Base
from ord_people.services.auth import AuthService
from ord_people.services.comment import CommentService
from ord_people.services.post import PostService
from ord_people.services.reaction import ReactionService
from ord_people.services.tag import TagService
from ord_people.services.user import UserService
from tests.helpers.fakes import FakeImageProcessor, FakeStorage

TEST_REDIS_DB = 15


pytest_plugins = [
    "tests.factories",
    "tests.helpers.auth_fixtures",
]


@pytest_asyncio.fixture
async def engine():
    eng = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield eng
    finally:
        await eng.dispose()


@pytest_asyncio.fixture
async def session_factory(engine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)


@pytest_asyncio.fixture
async def db_session(session_factory) -> AsyncIterator[AsyncSession]:
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def redis_client() -> AsyncIterator[redis.Redis]:
    client = redis.from_url(f"redis://localhost:6379/{TEST_REDIS_DB}")
    await client.flushdb()
    try:
        yield client
    finally:
        await client.flushdb()
        await client.aclose()


@pytest.fixture
def storage() -> FakeStorage:
    return FakeStorage()


@pytest.fixture
def image_processor() -> FakeImageProcessor:
    return FakeImageProcessor()


@pytest.fixture
def hasher() -> Argon2PasswordHasher:
    return Argon2PasswordHasher(pepper="test-pepper", time_cost=1, memory_cost=8192)


@pytest.fixture
def signer() -> ItsDangerousSessionSigner:
    return ItsDangerousSessionSigner(secret_key="test-secret", max_age=3600)


@pytest_asyncio.fixture
async def session_repository(redis_client) -> RedisSessionRepository:
    return RedisSessionRepository(redis_client, ttl=3600)


@pytest.fixture
def cache(redis_client) -> RedisCache:
    return RedisCache(redis_client)


@pytest.fixture
def rate_limiter(redis_client) -> RateLimiter:
    return RateLimiter(redis_client)


@pytest_asyncio.fixture
async def user_service(
    session_factory, cache, storage, image_processor, session_repository
) -> UserService:
    return UserService(
        session_factory, cache, storage, image_processor, session_repository
    )


@pytest_asyncio.fixture
async def auth_service(
    session_factory, hasher, session_repository, signer, user_service
) -> AuthService:
    return AuthService(
        session_factory, hasher, session_repository, signer, user_service
    )


@pytest_asyncio.fixture
async def post_service(session_factory, cache, storage, image_processor) -> PostService:
    return PostService(session_factory, cache, storage, image_processor)


@pytest_asyncio.fixture
async def comment_service(session_factory, storage) -> CommentService:
    return CommentService(session_factory, storage)


@pytest_asyncio.fixture
async def reaction_service(session_factory, cache) -> ReactionService:
    return ReactionService(session_factory, cache)


@pytest_asyncio.fixture
async def tag_service(session_factory, cache) -> TagService:
    return TagService(session_factory, cache)


@pytest_asyncio.fixture
async def app(
    session_factory: async_sessionmaker[Any],
    redis_client: redis.Redis,
    auth_service: AuthService,
    user_service: UserService,
    post_service: PostService,
    comment_service: CommentService,
    reaction_service: ReactionService,
    tag_service: TagService,
    cache: RedisCache,
    storage: FakeStorage,
    rate_limiter: RateLimiter,
) -> AsyncIterator[FastAPI]:
    application = FastAPI()
    application.state.session_factory = session_factory
    application.state.redis = redis_client
    application.state.cache = cache
    application.state.storage = storage
    application.state.auth_service = auth_service
    application.state.user_service = user_service
    application.state.post_service = post_service
    application.state.comment_service = comment_service
    application.state.reaction_service = reaction_service
    application.state.tag_service = tag_service
    application.state.rate_limiter = rate_limiter

    @application.exception_handler(AppError)
    async def _app_error(_, exc: AppError):
        return JSONResponse(
            status_code=exc.status_code, content={"detail": exc.detail}
        )

    @application.exception_handler(RequestValidationError)
    async def _validation(_, exc: RequestValidationError):
        from fastapi.encoders import jsonable_encoder

        return JSONResponse(
            status_code=422, content={"detail": jsonable_encoder(exc.errors())}
        )

    application.include_router(api_router)
    yield application


@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as c:
        yield c
