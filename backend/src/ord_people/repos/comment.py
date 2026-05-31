from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from ord_people.models.comment import Comment

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class CommentRepo:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, comment_id: int) -> Comment | None:
        logger.debug("comment_repo_get_by_id comment_id=%d", comment_id)
        return await self._session.get(Comment, comment_id)

    async def create(self, *, post_id: int, author_id: int, text: str) -> Comment:
        comment = Comment(post_id=post_id, author_id=author_id, text=text)
        self._session.add(comment)
        await self._session.flush()
        logger.info(
            "comment_repo_created comment_id=%d post_id=%d author_id=%d",
            comment.pk,
            post_id,
            author_id,
        )
        return comment

    async def update(self, comment: Comment, *, text: str) -> Comment:
        comment.text = text
        await self._session.flush()
        logger.debug("comment_repo_updated comment_id=%d", comment.pk)
        return comment

    async def delete(self, comment: Comment) -> None:
        comment_id = comment.pk
        await self._session.delete(comment)
        await self._session.flush()
        logger.info("comment_repo_deleted comment_id=%d", comment_id)

    async def list_by_post(
        self, post_id: int, *, limit: int, offset: int
    ) -> list[Comment]:
        stmt = (
            select(Comment)
            .options(selectinload(Comment.author))
            .where(Comment.post_id == post_id)
            .order_by(Comment.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list((await self._session.execute(stmt)).scalars())

    async def count_by_post(self, post_id: int) -> int:
        stmt = select(func.count(Comment.pk)).where(Comment.post_id == post_id)
        return int((await self._session.execute(stmt)).scalar_one())
