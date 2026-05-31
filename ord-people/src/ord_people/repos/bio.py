from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from sqlalchemy import select

from ord_people.models.bio import Bio

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class BioRepo:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_user(self, user_id: int) -> Bio | None:
        stmt = select(Bio).where(Bio.user_id == user_id)
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def delete_for_user(self, user_id: int) -> None:
        bio = await self.get_by_user(user_id)
        if bio is not None:
            await self._session.delete(bio)
            await self._session.flush()
            logger.info("bio_repo_deleted user_id=%d", user_id)
        else:
            logger.debug("bio_repo_delete_noop user_id=%d", user_id)

    async def upsert(self, user_id: int, **fields: object) -> Bio:
        bio = await self.get_by_user(user_id)
        action = "updated"
        if bio is None:
            bio = Bio(user_id=user_id, **fields)
            self._session.add(bio)
            action = "created"
        else:
            for k, v in fields.items():
                setattr(bio, k, v)
        await self._session.flush()
        logger.info(
            "bio_repo_upsert user_id=%d action=%s fields=%s",
            user_id,
            action,
            list(fields.keys()),
        )
        return bio
