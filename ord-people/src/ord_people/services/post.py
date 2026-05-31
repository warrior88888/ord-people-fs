from __future__ import annotations

import contextlib
import datetime
import logging
from typing import TYPE_CHECKING

from pydantic import BaseModel

from ord_people.config.constatns.cache import FEED_TTL, FEED_VERSION_KEY, POST_TTL
from ord_people.db.uow import UnitOfWork
from ord_people.exceptions import ForbiddenError, PostNotFoundError, UserNotFoundError
from ord_people.infra.utils.id_factory import generate_object_key
from ord_people.schemas.pagination import PaginatedResult
from ord_people.schemas.post import (
    PostCreateSchema,
    PostFeedFilters,
    PostLightSchema,
    PostSchema,
    PostUpdateSchema,
)
from ord_people.schemas.reaction import ReactionCountsSchema
from ord_people.schemas.tag import TagSchema
from ord_people.schemas.user import UserLightSchema
from ord_people.utils.enums import PostCategory, ReactionType


class _PostCachePayload(BaseModel):
    pk: int
    name: str
    description: str
    category: PostCategory
    photo_url: str | None = None
    external_url: str | None = None
    author_id: int
    tags: list[TagSchema]
    reactions: ReactionCountsSchema
    created_at: datetime.datetime
    updated_at: datetime.datetime


if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from ord_people.infra.cache.redis import RedisCache
    from ord_people.infra.media.image_processor import PillowImageProcessor
    from ord_people.infra.storage.s3 import S3FileStorage
    from ord_people.models.post import Post


logger = logging.getLogger(__name__)


class PostService:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        cache: RedisCache,
        storage: S3FileStorage,
        image: PillowImageProcessor,
    ) -> None:
        self._session_factory = session_factory
        self._cache = cache
        self._storage = storage
        self._image = image

    @staticmethod
    def _cache_key(post_id: int) -> str:
        return f"post:{post_id}"

    async def _feed_cache_key(self, *, limit: int, offset: int) -> str:
        version = await self._cache.get(FEED_VERSION_KEY) or "0"
        return f"feed:lite:v{version}:l{limit}:o{offset}"

    async def _invalidate_feed_cache(self) -> None:
        new_version = await self._cache.incr(FEED_VERSION_KEY)
        logger.debug("posts_feed_cache_invalidated version=%d", new_version)

    def _to_light(self, post: Post) -> PostLightSchema:
        return PostLightSchema(
            pk=post.pk,
            name=post.name,
            category=post.category,
            photo_url=self._storage.public_url(post.photo_key),
            created_at=post.created_at,
        )

    def _to_full(
        self,
        post: Post,
        counts: dict[ReactionType, int],
        my_reaction: ReactionType | None,
    ) -> PostSchema:
        return PostSchema(
            pk=post.pk,
            name=post.name,
            description=post.description,
            category=post.category,
            photo_url=self._storage.public_url(post.photo_key),
            external_url=post.external_url,
            author=UserLightSchema(
                pk=post.author.pk,
                username=post.author.username,
                first_name=post.author.first_name,
                last_name=post.author.last_name,
                avatar_url=self._storage.public_url(post.author.avatar_key),
            ),
            tags=[TagSchema.model_validate(t) for t in post.tags],
            reactions=ReactionCountsSchema(
                like=counts.get(ReactionType.LIKE, 0),
                support=counts.get(ReactionType.SUPPORT, 0),
                inspiring=counts.get(ReactionType.INSPIRING, 0),
            ),
            my_reaction=my_reaction,
            created_at=post.created_at,
            updated_at=post.updated_at,
        )

    def _author_light(self, user) -> UserLightSchema:
        return UserLightSchema(
            pk=user.pk,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            avatar_url=self._storage.public_url(user.avatar_key),
        )

    def _payload_from_full(
        self, post: Post, counts: dict[ReactionType, int]
    ) -> _PostCachePayload:
        return _PostCachePayload(
            pk=post.pk,
            name=post.name,
            description=post.description,
            category=post.category,
            photo_url=self._storage.public_url(post.photo_key),
            external_url=post.external_url,
            author_id=post.author_id,
            tags=[TagSchema.model_validate(t) for t in post.tags],
            reactions=ReactionCountsSchema(
                like=counts.get(ReactionType.LIKE, 0),
                support=counts.get(ReactionType.SUPPORT, 0),
                inspiring=counts.get(ReactionType.INSPIRING, 0),
            ),
            created_at=post.created_at,
            updated_at=post.updated_at,
        )

    def _assemble(
        self,
        payload: _PostCachePayload,
        author: UserLightSchema,
        my_reaction: ReactionType | None,
    ) -> PostSchema:
        return PostSchema(
            pk=payload.pk,
            name=payload.name,
            description=payload.description,
            category=payload.category,
            photo_url=payload.photo_url,
            external_url=payload.external_url,
            author=author,
            tags=payload.tags,
            reactions=payload.reactions,
            my_reaction=my_reaction,
            created_at=payload.created_at,
            updated_at=payload.updated_at,
        )

    async def get(self, post_id: int, *, current_user_id: int | None) -> PostSchema:
        cached = await self._cache.get(self._cache_key(post_id))
        if cached:
            logger.debug("post_cache_hit post_id=%d", post_id)
            payload = _PostCachePayload.model_validate_json(cached)
            async with UnitOfWork(self._session_factory) as uow:
                author_user = await uow.users.get_by_id(payload.author_id)
                if author_user is None:
                    await self._cache.delete(self._cache_key(post_id))
                    return await self._get_from_db(
                        post_id, current_user_id=current_user_id
                    )
                author = self._author_light(author_user)
                my_reaction: ReactionType | None = None
                if current_user_id is not None:
                    r = await uow.reactions.get(post_id, current_user_id)
                    my_reaction = r.reaction if r else None
            return self._assemble(payload, author, my_reaction)

        logger.debug("post_cache_miss post_id=%d", post_id)
        return await self._get_from_db(post_id, current_user_id=current_user_id)

    async def _get_from_db(
        self, post_id: int, *, current_user_id: int | None
    ) -> PostSchema:
        async with UnitOfWork(self._session_factory) as uow:
            post = await uow.posts.get_by_id(post_id)
            if post is None:
                logger.info("post_not_found post_id=%d", post_id)
                raise PostNotFoundError
            counts = await uow.reactions.counts_for_post(post_id)
            my: ReactionType | None = None
            if current_user_id is not None:
                r = await uow.reactions.get(post_id, current_user_id)
                my = r.reaction if r else None
            payload = self._payload_from_full(post, counts)
            author = self._author_light(post.author)
        await self._cache.setex(
            self._cache_key(post_id), POST_TTL, payload.model_dump_json()
        )
        logger.debug("post_cached post_id=%d ttl=%d", post_id, POST_TTL)
        return self._assemble(payload, author, my)

    async def create(self, author_id: int, data: PostCreateSchema) -> PostSchema:
        logger.info(
            "post_create_attempt author_id=%d name=%s category=%s tags=%d",
            author_id,
            data.name,
            data.category,
            len(data.tag_ids),
        )
        async with UnitOfWork(self._session_factory) as uow:
            if await uow.users.get_by_id(author_id) is None:
                logger.warning("post_create_author_missing author_id=%d", author_id)
                raise UserNotFoundError
            tags = await uow.tags.list_by_ids(data.tag_ids)
            post = await uow.posts.create(
                author_id=author_id,
                name=data.name,
                description=data.description,
                category=data.category,
                external_url=str(data.external_url) if data.external_url else None,
                tags=tags,
            )
            post = await uow.posts.get_by_id(post.pk)
            if post is None:
                logger.error("post_create_lookup_failed pk=after_insert")
                raise PostNotFoundError
            result = self._to_full(post, {}, None)
            post_id = post.pk
        await self._invalidate_feed_cache()
        logger.info("post_created post_id=%d author_id=%d", post_id, author_id)
        return result

    async def update(
        self, post_id: int, current_user_id: int, data: PostUpdateSchema
    ) -> PostSchema:
        logger.info(
            "post_update_attempt post_id=%d user_id=%d", post_id, current_user_id
        )
        async with UnitOfWork(self._session_factory) as uow:
            post = await uow.posts.get_by_id(post_id)
            if post is None:
                logger.info("post_update_not_found post_id=%d", post_id)
                raise PostNotFoundError
            if post.author_id != current_user_id:
                logger.warning(
                    "post_update_forbidden post_id=%d user_id=%d author_id=%d",
                    post_id,
                    current_user_id,
                    post.author_id,
                )
                raise ForbiddenError
            tags = None
            if data.tag_ids is not None:
                tags = await uow.tags.list_by_ids(data.tag_ids)
            update_fields = data.model_dump(exclude_unset=True, exclude={"tag_ids"})
            if update_fields.get("external_url"):
                update_fields["external_url"] = str(update_fields["external_url"])
            await uow.posts.update(post, tags=tags, **update_fields)
            counts = await uow.reactions.counts_for_post(post_id)
            r = await uow.reactions.get(post_id, current_user_id)
            result = self._to_full(post, counts, r.reaction if r else None)
        await self._cache.delete(self._cache_key(post_id))
        await self._invalidate_feed_cache()
        logger.info(
            "post_updated post_id=%d fields=%s tags_changed=%s",
            post_id,
            list(update_fields.keys()),
            tags is not None,
        )
        return result

    async def delete(self, post_id: int, current_user_id: int, is_admin: bool) -> None:
        logger.info(
            "post_delete_attempt post_id=%d user_id=%d is_admin=%s",
            post_id,
            current_user_id,
            is_admin,
        )
        async with UnitOfWork(self._session_factory) as uow:
            post = await uow.posts.get_by_id(post_id, with_relations=False)
            if post is None:
                logger.info("post_delete_not_found post_id=%d", post_id)
                raise PostNotFoundError
            if post.author_id != current_user_id and not is_admin:
                logger.warning(
                    "post_delete_forbidden post_id=%d user_id=%d author_id=%d",
                    post_id,
                    current_user_id,
                    post.author_id,
                )
                raise ForbiddenError
            photo_key = post.photo_key
            await uow.posts.delete(post)
        await self._cache.delete(self._cache_key(post_id))
        await self._invalidate_feed_cache()
        if photo_key:
            with contextlib.suppress(Exception):
                await self._storage.delete(photo_key)
                logger.debug("post_photo_deleted key=%s", photo_key)
        logger.info("post_deleted post_id=%d", post_id)

    async def upload_photo(self, post_id: int, current_user_id: int, raw: bytes) -> str:
        logger.info(
            "post_photo_upload_attempt post_id=%d user_id=%d raw_bytes=%d",
            post_id,
            current_user_id,
            len(raw),
        )
        webp = await self._image.to_webp(raw)
        key = generate_object_key(prefix=f"posts/{post_id}")
        await self._storage.upload(key, webp, "image/webp")
        logger.debug("post_photo_storage_upload_ok key=%s bytes=%d", key, len(webp))
        async with UnitOfWork(self._session_factory) as uow:
            post = await uow.posts.get_by_id(post_id, with_relations=False)
            if post is None:
                logger.warning("post_photo_post_missing post_id=%d", post_id)
                raise PostNotFoundError
            if post.author_id != current_user_id:
                logger.warning(
                    "post_photo_forbidden post_id=%d user_id=%d author_id=%d",
                    post_id,
                    current_user_id,
                    post.author_id,
                )
                raise ForbiddenError
            old_key = post.photo_key
            await uow.posts.set_photo(post, key)
        if old_key:
            with contextlib.suppress(Exception):
                await self._storage.delete(old_key)
                logger.debug("post_old_photo_deleted key=%s", old_key)
        await self._cache.delete(self._cache_key(post_id))
        await self._invalidate_feed_cache()
        logger.info(
            "post_photo_uploaded post_id=%d key=%s bytes=%d",
            post_id,
            key,
            len(webp),
        )
        return self._storage.public_url(key) or ""

    async def delete_photo(self, post_id: int, current_user_id: int) -> None:
        logger.info(
            "post_photo_delete_attempt post_id=%d user_id=%d",
            post_id,
            current_user_id,
        )
        async with UnitOfWork(self._session_factory) as uow:
            post = await uow.posts.get_by_id(post_id, with_relations=False)
            if post is None:
                logger.warning("post_photo_delete_post_missing post_id=%d", post_id)
                raise PostNotFoundError
            if post.author_id != current_user_id:
                logger.warning(
                    "post_photo_delete_forbidden post_id=%d user_id=%d author_id=%d",
                    post_id,
                    current_user_id,
                    post.author_id,
                )
                raise ForbiddenError
            old_key = post.photo_key
            if old_key is None:
                logger.debug("post_photo_delete_noop post_id=%d", post_id)
                return
            await uow.posts.set_photo(post, None)
        with contextlib.suppress(Exception):
            await self._storage.delete(old_key)
            logger.debug("post_photo_storage_deleted key=%s", old_key)
        await self._cache.delete(self._cache_key(post_id))
        await self._invalidate_feed_cache()
        logger.info("post_photo_deleted post_id=%d key=%s", post_id, old_key)

    @staticmethod
    def _is_cacheable_feed(filters: PostFeedFilters, author_id: int | None) -> bool:
        return (
            author_id is None
            and filters.category is None
            and not filters.tag_ids
            and filters.date_from is None
            and filters.date_to is None
        )

    async def list_feed(
        self,
        *,
        limit: int,
        offset: int,
        filters: PostFeedFilters,
        author_id: int | None = None,
    ) -> PaginatedResult[PostLightSchema]:
        cacheable = self._is_cacheable_feed(filters, author_id)
        cache_key: str | None = None
        if cacheable:
            cache_key = await self._feed_cache_key(limit=limit, offset=offset)
            cached = await self._cache.get(cache_key)
            if cached:
                logger.debug("posts_feed_cache_hit limit=%d offset=%d", limit, offset)
                return PaginatedResult[PostLightSchema].model_validate_json(cached)
        logger.debug(
            "posts_feed_query limit=%d offset=%d author_id=%s"
            " category=%s tags=%d cacheable=%s",
            limit,
            offset,
            author_id,
            filters.category,
            len(filters.tag_ids or []),
            cacheable,
        )
        async with UnitOfWork(self._session_factory) as uow:
            posts = await uow.posts.list_feed(
                limit=limit,
                offset=offset,
                author_id=author_id,
                category=filters.category,
                tag_ids=filters.tag_ids,
                date_from=filters.date_from,
                date_to=filters.date_to,
            )
            total = await uow.posts.count_feed(
                author_id=author_id,
                category=filters.category,
                tag_ids=filters.tag_ids,
                date_from=filters.date_from,
                date_to=filters.date_to,
            )
            items = [self._to_light(p) for p in posts]
        result = PaginatedResult[PostLightSchema](
            items=items, total=total, limit=limit, offset=offset
        )
        if cacheable and cache_key is not None:
            await self._cache.setex(cache_key, FEED_TTL, result.model_dump_json())
        logger.info(
            "posts_feed_listed limit=%d offset=%d returned=%d total=%d",
            limit,
            offset,
            len(items),
            total,
        )
        return result
