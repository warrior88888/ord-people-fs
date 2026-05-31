from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from ord_people.models.tag import Tag

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class TagRepo:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, tag_id: int) -> Tag | None:
        return await self._session.get(Tag, tag_id)

    async def list_all(self) -> list[Tag]:
        stmt = select(Tag).order_by(Tag.name)
        return list((await self._session.execute(stmt)).scalars())

    async def list_by_ids(self, ids: list[int]) -> list[Tag]:
        if not ids:
            return []
        stmt = select(Tag).where(Tag.pk.in_(ids))
        return list((await self._session.execute(stmt)).scalars())

    async def create(self, name: str) -> Tag:
        tag = Tag(name=name)
        self._session.add(tag)
        try:
            await self._session.flush()
        except IntegrityError as e:
            await self._session.rollback()
            logger.info("tag_repo_create_conflict name=%s", name)
            raise e
        logger.info("tag_repo_created tag_id=%d name=%s", tag.pk, name)
        return tag
