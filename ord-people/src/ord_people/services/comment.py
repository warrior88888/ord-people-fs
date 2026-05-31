from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ord_people.db.uow import UnitOfWork
from ord_people.exceptions import (
    CommentNotFoundError,
    ForbiddenError,
    PostNotFoundError,
    UserNotFoundError,
)
from ord_people.schemas.comment import (
    CommentCreateSchema,
    CommentSchema,
    CommentUpdateSchema,
)
from ord_people.schemas.pagination import PaginatedResult
from ord_people.schemas.user import UserLightSchema

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from ord_people.infra.storage.s3 import S3FileStorage
    from ord_people.models.comment import Comment
    from ord_people.models.user import User

logger = logging.getLogger(__name__)


class CommentService:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        storage: S3FileStorage,
    ) -> None:
        self._session_factory = session_factory
        self._storage = storage

    def _build(self, comment: Comment, author: User) -> CommentSchema:
        return CommentSchema(
            pk=comment.pk,
            text=comment.text,
            author=UserLightSchema(
                pk=author.pk,
                username=author.username,
                first_name=author.first_name,
                last_name=author.last_name,
                avatar_url=self._storage.public_url(author.avatar_key),
            ),
            created_at=comment.created_at,
            updated_at=comment.updated_at,
        )

    async def list_by_post(
        self, post_id: int, *, limit: int, offset: int
    ) -> PaginatedResult[CommentSchema]:
        async with UnitOfWork(self._session_factory) as uow:
            if await uow.posts.get_by_id(post_id, with_relations=False) is None:
                logger.info("comments_list_post_missing post_id=%d", post_id)
                raise PostNotFoundError
            comments = await uow.comments.list_by_post(
                post_id, limit=limit, offset=offset
            )
            total = await uow.comments.count_by_post(post_id)
            items = [self._build(c, c.author) for c in comments]
        logger.debug(
            "comments_listed post_id=%d limit=%d offset=%d returned=%d total=%d",
            post_id,
            limit,
            offset,
            len(items),
            total,
        )
        return PaginatedResult(items=items, total=total, limit=limit, offset=offset)

    async def create(
        self, post_id: int, author_id: int, data: CommentCreateSchema
    ) -> CommentSchema:
        logger.info(
            "comment_create_attempt post_id=%d author_id=%d", post_id, author_id
        )
        async with UnitOfWork(self._session_factory) as uow:
            if await uow.posts.get_by_id(post_id, with_relations=False) is None:
                logger.info("comment_create_post_missing post_id=%d", post_id)
                raise PostNotFoundError
            comment = await uow.comments.create(
                post_id=post_id, author_id=author_id, text=data.text
            )
            author = await uow.users.get_by_id(author_id)
            if author is None:
                logger.warning(
                    "comment_create_author_missing author_id=%d", author_id
                )
                raise UserNotFoundError
            result = self._build(comment, author)
        logger.info(
            "comment_created comment_id=%d post_id=%d author_id=%d",
            result.pk,
            post_id,
            author_id,
        )
        return result

    async def update(
        self,
        post_id: int,
        comment_id: int,
        current_user_id: int,
        data: CommentUpdateSchema,
    ) -> CommentSchema:
        logger.info(
            "comment_update_attempt comment_id=%d post_id=%d user_id=%d",
            comment_id,
            post_id,
            current_user_id,
        )
        async with UnitOfWork(self._session_factory) as uow:
            comment = await uow.comments.get_by_id(comment_id)
            if comment is None or comment.post_id != post_id:
                logger.info(
                    "comment_update_not_found comment_id=%d post_id=%d",
                    comment_id,
                    post_id,
                )
                raise CommentNotFoundError
            if comment.author_id != current_user_id:
                logger.warning(
                    "comment_update_forbidden comment_id=%d user_id=%d author_id=%d",
                    comment_id,
                    current_user_id,
                    comment.author_id,
                )
                raise ForbiddenError
            await uow.comments.update(comment, text=data.text)
            author = await uow.users.get_by_id(current_user_id)
            if author is None:
                logger.warning(
                    "comment_update_author_missing user_id=%d", current_user_id
                )
                raise UserNotFoundError
            result = self._build(comment, author)
        logger.info("comment_updated comment_id=%d", comment_id)
        return result

    async def delete(
        self,
        post_id: int,
        comment_id: int,
        current_user_id: int,
        is_admin: bool,
    ) -> None:
        logger.info(
            "comment_delete_attempt comment_id=%d post_id=%d user_id=%d is_admin=%s",
            comment_id,
            post_id,
            current_user_id,
            is_admin,
        )
        async with UnitOfWork(self._session_factory) as uow:
            comment = await uow.comments.get_by_id(comment_id)
            if comment is None or comment.post_id != post_id:
                logger.info(
                    "comment_delete_not_found comment_id=%d post_id=%d",
                    comment_id,
                    post_id,
                )
                raise CommentNotFoundError
            if comment.author_id != current_user_id and not is_admin:
                logger.warning(
                    "comment_delete_forbidden comment_id=%d user_id=%d author_id=%d",
                    comment_id,
                    current_user_id,
                    comment.author_id,
                )
                raise ForbiddenError
            await uow.comments.delete(comment)
        logger.info("comment_deleted comment_id=%d", comment_id)
