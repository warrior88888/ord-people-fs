from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from sqlalchemy import delete, func, select

from ord_people.models.reaction import Reaction

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from ord_people.utils.enums import ReactionType

logger = logging.getLogger(__name__)


class ReactionRepo:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, post_id: int, user_id: int) -> Reaction | None:
        stmt = select(Reaction).where(
            Reaction.post_id == post_id, Reaction.user_id == user_id
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def set(self, post_id: int, user_id: int, reaction: ReactionType) -> Reaction:
        existing = await self.get(post_id, user_id)
        if existing is None:
            existing = Reaction(post_id=post_id, user_id=user_id, reaction=reaction)
            self._session.add(existing)
            logger.debug(
                "reaction_repo_inserted post_id=%d user_id=%d reaction=%s",
                post_id,
                user_id,
                reaction,
            )
        else:
            existing.reaction = reaction
            logger.debug(
                "reaction_repo_updated post_id=%d user_id=%d reaction=%s",
                post_id,
                user_id,
                reaction,
            )
        await self._session.flush()
        return existing

    async def delete(self, post_id: int, user_id: int) -> None:
        stmt = delete(Reaction).where(
            Reaction.post_id == post_id, Reaction.user_id == user_id
        )
        await self._session.execute(stmt)
        await self._session.flush()
        logger.debug(
            "reaction_repo_deleted post_id=%d user_id=%d", post_id, user_id
        )

    async def counts_for_post(self, post_id: int) -> dict[ReactionType, int]:
        stmt = (
            select(Reaction.reaction, func.count())
            .where(Reaction.post_id == post_id)
            .group_by(Reaction.reaction)
        )
        rows = (await self._session.execute(stmt)).all()
        return {r: int(c) for r, c in rows}
