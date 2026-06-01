import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from ord_people.config.settings import get_settings
from ord_people.infra.auth.password_hasher import Argon2PasswordHasher
from ord_people.infra.auth.session_repository import RedisSessionRepository
from ord_people.infra.auth.session_signer import ItsDangerousSessionSigner
from ord_people.infra.cache.redis import RedisCache
from ord_people.infra.media.image_processor import PillowImageProcessor
from ord_people.infra.rate_limit import RateLimiter
from ord_people.infra.storage.s3 import S3FileStorage
from ord_people.services.auth import AuthService
from ord_people.services.comment import CommentService
from ord_people.services.post import PostService
from ord_people.services.reaction import ReactionService
from ord_people.services.tag import TagService
from ord_people.services.user import UserService

logger = logging.getLogger(__name__)


def build_lifespan(engine, session_factory, redis_client):
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        settings = get_settings()
        logger.info(
            "lifespan_startup debug=%s behind_proxy=%s root_path=%s log_level=%s",
            settings.app.debug,
            settings.app.behind_proxy,
            settings.app.root_path,
            settings.log.level,
        )

        cache = RedisCache(redis_client)
        storage = S3FileStorage(settings.s3)
        image = PillowImageProcessor()
        logger.debug("infra_wired cache=redis storage=s3 image=pillow")

        hasher = Argon2PasswordHasher(
            pepper=settings.auth.pepper,
            time_cost=settings.auth.argon2_time_cost,
            memory_cost=settings.auth.argon2_memory_cost,
        )
        session_repo = RedisSessionRepository(
            redis_client, ttl=settings.auth.session_ttl
        )
        signer = ItsDangerousSessionSigner(
            secret_key=settings.app.secret_key.get_secret_value(),
            max_age=settings.auth.session_ttl,
        )
        logger.debug(
            "auth_wired argon2_time_cost=%d argon2_memory_cost=%d session_ttl=%d",
            settings.auth.argon2_time_cost,
            settings.auth.argon2_memory_cost,
            settings.auth.session_ttl,
        )

        app.state.settings = settings
        app.state.engine = engine
        app.state.session_factory = session_factory
        app.state.redis = redis_client
        app.state.cache = cache
        app.state.storage = storage

        app.state.user_service = UserService(
            session_factory, cache, storage, image, session_repo
        )
        app.state.auth_service = AuthService(
            session_factory, hasher, session_repo, signer, app.state.user_service
        )
        app.state.post_service = PostService(session_factory, cache, storage, image)
        app.state.comment_service = CommentService(session_factory, storage)
        app.state.reaction_service = ReactionService(session_factory, cache)
        app.state.tag_service = TagService(session_factory, cache)
        app.state.rate_limiter = RateLimiter(redis_client)
        logger.info("services_initialized")

        try:
            await redis_client.ping()
            logger.info("startup_ok redis_ping=ok")
        except Exception:
            logger.exception("startup_redis_ping_failed")

        try:
            yield
        finally:
            logger.info("shutdown_begin")
            try:
                await cache.close()
                logger.debug("cache_closed")
            except Exception:
                logger.exception("cache_close_failed")
            try:
                await engine.dispose()
                logger.debug("engine_disposed")
            except Exception:
                logger.exception("engine_dispose_failed")
            logger.info("shutdown_complete")

    return lifespan
