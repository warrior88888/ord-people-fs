from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Self

from ord_people.repos.bio import BioRepo
from ord_people.repos.comment import CommentRepo
from ord_people.repos.post import PostRepo
from ord_people.repos.reaction import ReactionRepo
from ord_people.repos.tag import TagRepo
from ord_people.repos.user import UserRepo

if TYPE_CHECKING:
    from types import TracebackType

    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

logger = logging.getLogger(__name__)


class UnitOfWork:
    session: AsyncSession
    users: UserRepo
    bios: BioRepo
    posts: PostRepo
    tags: TagRepo
    comments: CommentRepo
    reactions: ReactionRepo

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def __aenter__(self) -> Self:
        self.session = self._session_factory()
        self.users = UserRepo(self.session)
        self.bios = BioRepo(self.session)
        self.posts = PostRepo(self.session)
        self.tags = TagRepo(self.session)
        self.comments = CommentRepo(self.session)
        self.reactions = ReactionRepo(self.session)
        logger.debug("uow_open")
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        try:
            if exc_type is None:
                await self.session.commit()
                logger.debug("uow_commit")
            else:
                await self.session.rollback()
                logger.warning(
                    "uow_rollback exc=%s",
                    exc_type.__name__ if exc_type else "unknown",
                )
        finally:
            await self.session.close()
            logger.debug("uow_close")

    async def commit(self) -> None:
        await self.session.commit()
        logger.debug("uow_explicit_commit")

    async def rollback(self) -> None:
        await self.session.rollback()
        logger.debug("uow_explicit_rollback")

    async def flush(self) -> None:
        await self.session.flush()
        logger.debug("uow_flush")
