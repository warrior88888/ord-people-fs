from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from ord_people.models.user import User

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class UserRepo:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: int) -> User | None:
        logger.debug("user_repo_get_by_id user_id=%d", user_id)
        return await self._session.get(User, user_id)

    async def get_by_username(
        self, username: str, *, with_bio: bool = False
    ) -> User | None:
        logger.debug(
            "user_repo_get_by_username username=%s with_bio=%s", username, with_bio
        )
        stmt = select(User).where(User.username == username, User.deleted_at.is_(None))
        if with_bio:
            stmt = stmt.options(selectinload(User.bio))
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def exists_by_username(self, username: str) -> bool:
        stmt = select(func.count()).select_from(User).where(User.username == username)
        return bool((await self._session.execute(stmt)).scalar_one())

    async def create(
        self,
        *,
        username: str,
        hashed_password: str,
        first_name: str,
        last_name: str,
        is_admin: bool = False,
    ) -> User:
        user = User(
            username=username,
            hashed_password=hashed_password,
            first_name=first_name,
            last_name=last_name,
            is_admin=is_admin,
        )
        self._session.add(user)
        await self._session.flush()
        logger.info(
            "user_repo_created user_id=%d username=%s is_admin=%s",
            user.pk,
            username,
            is_admin,
        )
        return user

    async def update(self, user: User, **fields: object) -> User:
        applied = {k: v for k, v in fields.items() if v is not None}
        for k, v in applied.items():
            setattr(user, k, v)
        await self._session.flush()
        logger.debug(
            "user_repo_updated user_id=%d fields=%s", user.pk, list(applied.keys())
        )
        return user

    async def set_avatar(self, user: User, key: str | None) -> User:
        user.avatar_key = key
        await self._session.flush()
        logger.debug("user_repo_set_avatar user_id=%d key=%s", user.pk, key)
        return user

    def _feed_stmt(self):
        return select(User).where(
            User.deleted_at.is_(None),
            User.is_active.is_(True),
        )

    async def list_feed(
        self,
        *,
        limit: int,
        offset: int,
    ) -> list[User]:
        stmt = (
            self._feed_stmt()
            .order_by(User.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        return list((await self._session.execute(stmt)).scalars())

    async def count_feed(self) -> int:
        stmt = self._feed_stmt().with_only_columns(func.count(User.pk))
        return int((await self._session.execute(stmt)).scalar_one())
