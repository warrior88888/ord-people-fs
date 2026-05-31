import logging

import redis.asyncio as redis
from fastapi import FastAPI

from ord_people.api import api_router
from ord_people.config.settings import get_settings
from ord_people.db.session import make_engine, make_session_factory
from ord_people.exception_handlers import register_exception_handlers
from ord_people.infra.logging import setup_logging
from ord_people.lifespan import build_lifespan
from ord_people.middleware import register_middleware

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    settings = get_settings()
    setup_logging(settings.log)
    logger.info(
        "create_app title=%s debug=%s root_path=%s",
        "ord-people-big-deals",
        settings.app.debug,
        settings.app.root_path,
    )

    engine = make_engine(settings)
    session_factory = make_session_factory(engine)
    redis_client = redis.from_url(settings.redis.url)
    logger.debug("redis_client_created url=%s", settings.redis.url)

    app = FastAPI(
        title="ord-people-big-deals",
        debug=settings.app.debug,
        root_path=settings.app.root_path,
        lifespan=build_lifespan(engine, session_factory, redis_client),
        docs_url="/docs" if settings.app.debug else None,
        redoc_url="/redoc" if settings.app.debug else None,
        openapi_url="/openapi.json" if settings.app.debug else None,
    )

    register_middleware(app, settings)
    register_exception_handlers(app)

    @app.get("/ht")
    async def healthcheck() -> dict[str, str]:
        logger.debug("healthcheck_hit")
        return {"status": "ok"}

    app.include_router(api_router)
    logger.debug("api_router_included")

    return app
