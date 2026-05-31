from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ord_people.db.uow import UnitOfWork
from ord_people.exceptions import PostNotFoundError
from ord_people.schemas.reaction import ReactionCountsSchema
from ord_people.utils.enums import ReactionType

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from ord_people.infra.cache.redis import RedisCache

logger = logging.getLogger(__name__)


class ReactionService:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        cache: RedisCache,
    ) -> None:
        self._session_factory = session_factory
        self._cache = cache

    async def toggle(
        self, post_id: int, user_id: int, reaction: ReactionType
    ) -> tuple[ReactionCountsSchema, ReactionType | None]:
        logger.info(
            "reaction_toggle_attempt post_id=%d user_id=%d reaction=%s",
            post_id,
            user_id,
            reaction,
        )
        async with UnitOfWork(self._session_factory) as uow:
            if await uow.posts.get_by_id(post_id, with_relations=False) is None:
                logger.info("reaction_post_missing post_id=%d", post_id)
                raise PostNotFoundError
            current = await uow.reactions.get(post_id, user_id)
            new_reaction: ReactionType | None
            if current is None:
                await uow.reactions.set(post_id, user_id, reaction)
                new_reaction = reaction
                action = "added"
            elif current.reaction == reaction:
                await uow.reactions.delete(post_id, user_id)
                new_reaction = None
                action = "removed"
            else:
                await uow.reactions.set(post_id, user_id, reaction)
                new_reaction = reaction
                action = "changed"
            counts = await uow.reactions.counts_for_post(post_id)
        await self._cache.delete(f"post:{post_id}")
        logger.info(
            "reaction_toggled post_id=%d user_id=%d action=%s reaction=%s",
            post_id,
            user_id,
            action,
            new_reaction,
        )
        return (
            ReactionCountsSchema(
                like=counts.get(ReactionType.LIKE, 0),
                support=counts.get(ReactionType.SUPPORT, 0),
                inspiring=counts.get(ReactionType.INSPIRING, 0),
            ),
            new_reaction,
        )
