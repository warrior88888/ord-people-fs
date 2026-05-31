from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from ord_people.models.post import Post
from ord_people.models.tag import Tag, post_tags

if TYPE_CHECKING:
    import datetime

    from sqlalchemy.ext.asyncio import AsyncSession

    from ord_people.utils.enums import PostCategory

logger = logging.getLogger(__name__)


class PostRepo:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(
        self, post_id: int, *, with_relations: bool = True
    ) -> Post | None:
        logger.debug(
            "post_repo_get_by_id post_id=%d with_relations=%s",
            post_id,
            with_relations,
        )
        stmt = select(Post).where(Post.pk == post_id)
        if with_relations:
            stmt = stmt.options(
                selectinload(Post.author),
                selectinload(Post.tags),
            )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def create(
        self,
        *,
        author_id: int,
        name: str,
        description: str,
        category: PostCategory,
        external_url: str | None,
        tags: list[Tag],
    ) -> Post:
        post = Post(
            author_id=author_id,
            name=name,
            description=description,
            category=category,
            external_url=external_url,
        )
        post.tags = tags
        self._session.add(post)
        await self._session.flush()
        logger.info(
            "post_repo_created post_id=%d author_id=%d category=%s tags=%d",
            post.pk,
            author_id,
            category,
            len(tags),
        )
        return post

    async def update(
        self,
        post: Post,
        *,
        tags: list[Tag] | None = None,
        **fields: object,
    ) -> Post:
        applied = {k: v for k, v in fields.items() if v is not None}
        for k, v in applied.items():
            setattr(post, k, v)
        if tags is not None:
            post.tags = tags
        await self._session.flush()
        logger.debug(
            "post_repo_updated post_id=%d fields=%s tags_replaced=%s",
            post.pk,
            list(applied.keys()),
            tags is not None,
        )
        return post

    async def delete(self, post: Post) -> None:
        post_id = post.pk
        await self._session.delete(post)
        await self._session.flush()
        logger.info("post_repo_deleted post_id=%d", post_id)

    async def set_photo(self, post: Post, key: str | None) -> Post:
        post.photo_key = key
        await self._session.flush()
        logger.debug("post_repo_set_photo post_id=%d key=%s", post.pk, key)
        return post

    def _feed_stmt(
        self,
        *,
        author_id: int | None = None,
        category: PostCategory | None = None,
        tag_ids: list[int] | None = None,
        date_from: datetime.datetime | None = None,
        date_to: datetime.datetime | None = None,
    ):
        stmt = select(Post)
        if author_id is not None:
            stmt = stmt.where(Post.author_id == author_id)
        if category is not None:
            stmt = stmt.where(Post.category == category)
        if date_from is not None:
            stmt = stmt.where(Post.created_at >= date_from)
        if date_to is not None:
            stmt = stmt.where(Post.created_at <= date_to)
        if tag_ids:
            stmt = (
                stmt.join(post_tags, post_tags.c.post_id == Post.pk)
                .where(post_tags.c.tag_id.in_(tag_ids))
                .group_by(Post.pk)
                .having(
                    func.count(func.distinct(post_tags.c.tag_id)) == len(set(tag_ids))
                )
            )
        return stmt

    async def list_feed(
        self,
        *,
        limit: int,
        offset: int,
        author_id: int | None = None,
        category: PostCategory | None = None,
        tag_ids: list[int] | None = None,
        date_from: datetime.datetime | None = None,
        date_to: datetime.datetime | None = None,
    ) -> list[Post]:
        stmt = (
            self._feed_stmt(
                author_id=author_id,
                category=category,
                tag_ids=tag_ids,
                date_from=date_from,
                date_to=date_to,
            )
            .order_by(Post.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list((await self._session.execute(stmt)).unique().scalars())

    async def count_feed(
        self,
        *,
        author_id: int | None = None,
        category: PostCategory | None = None,
        tag_ids: list[int] | None = None,
        date_from: datetime.datetime | None = None,
        date_to: datetime.datetime | None = None,
    ) -> int:
        if tag_ids:
            sub = (
                self._feed_stmt(
                    author_id=author_id,
                    category=category,
                    tag_ids=tag_ids,
                    date_from=date_from,
                    date_to=date_to,
                )
                .with_only_columns(Post.pk)
                .subquery()
            )
            stmt = select(func.count()).select_from(sub)
        else:
            stmt = select(func.count(Post.pk))
            if author_id is not None:
                stmt = stmt.where(Post.author_id == author_id)
            if category is not None:
                stmt = stmt.where(Post.category == category)
            if date_from is not None:
                stmt = stmt.where(Post.created_at >= date_from)
            if date_to is not None:
                stmt = stmt.where(Post.created_at <= date_to)
        return int((await self._session.execute(stmt)).scalar_one())
