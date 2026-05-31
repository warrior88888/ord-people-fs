from __future__ import annotations

import contextlib
import datetime
import logging
from typing import TYPE_CHECKING

from ord_people.config.constatns.cache import (
    USER_TTL,
    USERS_FEED_TTL,
    USERS_FEED_VERSION_KEY,
)
from ord_people.config.constatns.media import IMAGE_INPUT_MAX_SIZE
from ord_people.config.constatns.user import (
    DELETED_DISPLAY_FIRST_NAME,
    DELETED_DISPLAY_LAST_NAME,
)
from ord_people.db.uow import UnitOfWork
from ord_people.exceptions import AvatarTooLargeError, UserNotFoundError
from ord_people.infra.utils.id_factory import generate_object_key
from ord_people.schemas.bio import BioSchema, BioUpdateSchema
from ord_people.schemas.pagination import PaginatedResult
from ord_people.schemas.user import UserLightSchema, UserSchema, UserUpdateSchema

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from ord_people.infra.auth.session_repository import RedisSessionRepository
    from ord_people.infra.cache.redis import RedisCache
    from ord_people.infra.media.image_processor import PillowImageProcessor
    from ord_people.infra.storage.s3 import S3FileStorage


logger = logging.getLogger(__name__)


class UserService:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        cache: RedisCache,
        storage: S3FileStorage,
        image: PillowImageProcessor,
        sessions: RedisSessionRepository,
    ) -> None:
        self._session_factory = session_factory
        self._cache = cache
        self._storage = storage
        self._image = image
        self._sessions = sessions

    @staticmethod
    def _cache_key(username: str) -> str:
        return f"user:{username}"

    async def _feed_cache_key(self, *, limit: int, offset: int) -> str:
        version = await self._cache.get(USERS_FEED_VERSION_KEY) or "0"
        return f"users:feed:lite:v{version}:l{limit}:o{offset}"

    async def _invalidate_feed_cache(self) -> None:
        new_version = await self._cache.incr(USERS_FEED_VERSION_KEY)
        logger.debug("users_feed_cache_invalidated version=%d", new_version)

    def _user_to_light(self, user) -> UserLightSchema:
        return UserLightSchema(
            pk=user.pk,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            avatar_url=self._storage.public_url(user.avatar_key),
        )

    def _user_to_schema(self, user, bio) -> UserSchema:
        return UserSchema(
            pk=user.pk,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            avatar_url=self._storage.public_url(user.avatar_key),
            is_admin=user.is_admin,
            created_at=user.created_at,
            bio=BioSchema.model_validate(bio) if bio else None,
        )

    async def list_feed(
        self, *, limit: int, offset: int
    ) -> PaginatedResult[UserLightSchema]:
        cache_key = await self._feed_cache_key(limit=limit, offset=offset)
        cached = await self._cache.get(cache_key)
        if cached:
            logger.debug("users_feed_cache_hit limit=%d offset=%d", limit, offset)
            return PaginatedResult[UserLightSchema].model_validate_json(cached)
        logger.debug("users_feed_cache_miss limit=%d offset=%d", limit, offset)
        async with UnitOfWork(self._session_factory) as uow:
            users = await uow.users.list_feed(limit=limit, offset=offset)
            total = await uow.users.count_feed()
            items = [self._user_to_light(u) for u in users]
        result = PaginatedResult[UserLightSchema](
            items=items, total=total, limit=limit, offset=offset
        )
        await self._cache.setex(cache_key, USERS_FEED_TTL, result.model_dump_json())
        logger.info(
            "users_feed_listed limit=%d offset=%d returned=%d total=%d",
            limit,
            offset,
            len(items),
            total,
        )
        return result

    async def get_by_username(self, username: str) -> UserSchema:
        cached = await self._cache.get(self._cache_key(username))
        if cached:
            logger.debug("user_cache_hit username=%s", username)
            return UserSchema.model_validate_json(cached)
        logger.debug("user_cache_miss username=%s", username)
        async with UnitOfWork(self._session_factory) as uow:
            user = await uow.users.get_by_username(username, with_bio=True)
            if user is None:
                logger.info("user_not_found username=%s", username)
                raise UserNotFoundError
            bio = await user.awaitable_attrs.bio
            result = self._user_to_schema(user, bio)
        await self._cache.setex(
            self._cache_key(username), USER_TTL, result.model_dump_json()
        )
        logger.debug("user_cached username=%s ttl=%d", username, USER_TTL)
        return result

    async def update_me(self, user_id: int, data: UserUpdateSchema) -> UserSchema:
        logger.info("user_update_attempt user_id=%d", user_id)
        async with UnitOfWork(self._session_factory) as uow:
            user = await uow.users.get_by_id(user_id)
            if user is None:
                logger.warning("user_update_user_missing user_id=%d", user_id)
                raise UserNotFoundError
            fields = data.model_dump(exclude_unset=True)
            await uow.users.update(user, **fields)
            bio = await uow.bios.get_by_user(user_id)
            result = self._user_to_schema(user, bio)
            username = user.username
        await self._cache.delete(self._cache_key(username))
        await self._invalidate_feed_cache()
        logger.info(
            "user_updated user_id=%d username=%s fields=%s",
            user_id,
            username,
            list(fields.keys()),
        )
        return result

    async def update_bio(self, user_id: int, data: BioUpdateSchema) -> BioSchema:
        logger.info("bio_update_attempt user_id=%d", user_id)
        async with UnitOfWork(self._session_factory) as uow:
            user = await uow.users.get_by_id(user_id)
            if user is None:
                logger.warning("bio_update_user_missing user_id=%d", user_id)
                raise UserNotFoundError
            fields = data.model_dump(exclude_unset=True)
            bio = await uow.bios.upsert(user_id, **fields)
            schema = BioSchema.model_validate(bio)
            username = user.username
        await self._cache.delete(self._cache_key(username))
        logger.info("bio_updated user_id=%d fields=%s", user_id, list(fields.keys()))
        return schema

    async def upload_avatar(self, user_id: int, raw: bytes) -> str:
        logger.info("avatar_upload_attempt user_id=%d raw_bytes=%d", user_id, len(raw))
        if len(raw) > IMAGE_INPUT_MAX_SIZE:
            logger.warning(
                "avatar_raw_too_large user_id=%d size=%d max=%d",
                user_id,
                len(raw),
                IMAGE_INPUT_MAX_SIZE,
            )
            raise AvatarTooLargeError
        webp = await self._image.to_webp(raw)
        key = generate_object_key(prefix=f"avatars/{user_id}")
        await self._storage.upload(key, webp, "image/webp")
        logger.debug("avatar_storage_upload_ok key=%s bytes=%d", key, len(webp))
        async with UnitOfWork(self._session_factory) as uow:
            user = await uow.users.get_by_id(user_id)
            if user is None:
                logger.warning("avatar_upload_user_missing user_id=%d", user_id)
                raise UserNotFoundError
            old_key = user.avatar_key
            await uow.users.set_avatar(user, key)
            username = user.username
        if old_key:
            with contextlib.suppress(Exception):
                await self._storage.delete(old_key)
                logger.debug("avatar_old_deleted key=%s", old_key)
        await self._cache.delete(self._cache_key(username))
        await self._invalidate_feed_cache()
        logger.info(
            "avatar_uploaded user_id=%d key=%s bytes=%d",
            user_id,
            key,
            len(webp),
        )
        return self._storage.public_url(key) or ""

    async def delete_avatar(self, user_id: int) -> None:
        logger.info("avatar_delete_attempt user_id=%d", user_id)
        async with UnitOfWork(self._session_factory) as uow:
            user = await uow.users.get_by_id(user_id)
            if user is None:
                logger.warning("avatar_delete_user_missing user_id=%d", user_id)
                raise UserNotFoundError
            old_key = user.avatar_key
            if old_key is None:
                logger.debug("avatar_delete_noop user_id=%d", user_id)
                return
            await uow.users.set_avatar(user, None)
            username = user.username
        with contextlib.suppress(Exception):
            await self._storage.delete(old_key)
            logger.debug("avatar_storage_deleted key=%s", old_key)
        await self._cache.delete(self._cache_key(username))
        await self._invalidate_feed_cache()
        logger.info("avatar_deleted user_id=%d key=%s", user_id, old_key)

    async def delete_me(self, user_id: int) -> None:
        logger.info("user_delete_attempt user_id=%d", user_id)
        async with UnitOfWork(self._session_factory) as uow:
            user = await uow.users.get_by_id(user_id)
            if user is None:
                logger.warning("user_delete_user_missing user_id=%d", user_id)
                raise UserNotFoundError
            old_username = user.username
            old_avatar = user.avatar_key
            user.username = f"deleted-{user.pk}"
            user.first_name = DELETED_DISPLAY_FIRST_NAME
            user.last_name = DELETED_DISPLAY_LAST_NAME
            user.avatar_key = None
            user.hashed_password = ""
            user.is_active = False
            user.deleted_at = datetime.datetime.now(datetime.UTC)
            await uow.bios.delete_for_user(user_id)
            await uow.flush()
        if old_avatar:
            with contextlib.suppress(Exception):
                await self._storage.delete(old_avatar)
                logger.debug("avatar_deleted_on_user_delete key=%s", old_avatar)
        await self._cache.delete(self._cache_key(old_username))
        await self._invalidate_feed_cache()
        await self._sessions.delete_all_for_user(user_id)
        logger.info("user_anonymized user_id=%d old_username=%s", user_id, old_username)
