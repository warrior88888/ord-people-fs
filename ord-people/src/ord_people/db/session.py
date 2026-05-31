import logging
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

if TYPE_CHECKING:
    from ord_people.config.settings import Settings

logger = logging.getLogger(__name__)


def make_engine(settings: Settings) -> AsyncEngine:
    logger.info(
        "db_engine_create url=%s echo=%s pool_size=%d max_overflow=%d",
        settings.postgres.url,
        settings.app.debug,
        settings.postgres.pool_size,
        settings.postgres.max_overflow,
    )
    return create_async_engine(
        str(settings.postgres.url),
        echo=settings.app.debug,
        pool_pre_ping=True,
        pool_size=settings.postgres.pool_size,
        max_overflow=settings.postgres.max_overflow,
    )


def make_session_factory(
    engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    logger.debug("db_session_factory_create")
    return async_sessionmaker(
        bind=engine,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )
