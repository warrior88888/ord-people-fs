from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from pydantic import TypeAdapter
from sqlalchemy.exc import IntegrityError

from ord_people.config.constatns.cache import TAGS_CACHE_KEY, TAGS_TTL
from ord_people.db.uow import UnitOfWork
from ord_people.exceptions import TagAlreadyExistsError
from ord_people.schemas.tag import TagCreateSchema, TagSchema

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from ord_people.infra.cache.redis import RedisCache

logger = logging.getLogger(__name__)

_TAGS_ADAPTER: TypeAdapter[list[TagSchema]] = TypeAdapter(list[TagSchema])


class TagService:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        cache: RedisCache,
    ) -> None:
        self._session_factory = session_factory
        self._cache = cache

    async def _invalidate_cache(self) -> None:
        await self._cache.delete(TAGS_CACHE_KEY)
        logger.debug("tags_cache_invalidated")

    async def list_all(self) -> list[TagSchema]:
        cached = await self._cache.get(TAGS_CACHE_KEY)
        if cached:
            logger.debug("tags_cache_hit")
            return _TAGS_ADAPTER.validate_json(cached)
        logger.debug("tags_cache_miss")
        async with UnitOfWork(self._session_factory) as uow:
            tags = await uow.tags.list_all()
            schemas = [TagSchema.model_validate(t) for t in tags]
        await self._cache.setex(
            TAGS_CACHE_KEY, TAGS_TTL, _TAGS_ADAPTER.dump_json(schemas).decode()
        )
        logger.info("tags_listed count=%d ttl=%d", len(schemas), TAGS_TTL)
        return schemas

    async def create(self, data: TagCreateSchema) -> TagSchema:
        logger.info("tag_create_attempt name=%s", data.name)
        try:
            async with UnitOfWork(self._session_factory) as uow:
                tag = await uow.tags.create(data.name)
                schema = TagSchema.model_validate(tag)
        except IntegrityError as e:
            logger.info("tag_create_conflict name=%s", data.name)
            raise TagAlreadyExistsError from e
        await self._invalidate_cache()
        logger.info("tag_created tag_id=%d name=%s", schema.pk, schema.name)
        return schema
