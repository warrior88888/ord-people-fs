from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ord_people.db.uow import UnitOfWork
from ord_people.exceptions import InvalidCredentialsError, UsernameAlreadyTakenError

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from ord_people.infra.auth.password_hasher import Argon2PasswordHasher
    from ord_people.infra.auth.session_repository import RedisSessionRepository
    from ord_people.infra.auth.session_signer import ItsDangerousSessionSigner
    from ord_people.schemas.auth import LoginSchema, RegisterSchema
    from ord_people.services.user import UserService

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        hasher: Argon2PasswordHasher,
        sessions: RedisSessionRepository,
        signer: ItsDangerousSessionSigner,
        users: UserService,
    ) -> None:
        self._session_factory = session_factory
        self._hasher = hasher
        self._sessions = sessions
        self._signer = signer
        self._users = users

    async def register(self, data: RegisterSchema) -> tuple[int, str]:
        logger.info("register_attempt username=%s", data.username)
        async with UnitOfWork(self._session_factory) as uow:
            if await uow.users.exists_by_username(data.username):
                logger.info("register_conflict username=%s", data.username)
                raise UsernameAlreadyTakenError
            hashed = await self._hasher.hash(data.password)
            user = await uow.users.create(
                username=data.username,
                hashed_password=hashed,
                first_name=data.first_name,
                last_name=data.last_name,
            )
            user_id = user.pk
            username = user.username
        await self._users.invalidate_feed_cache()
        logger.info("user_registered user_id=%d username=%s", user_id, username)
        return user_id, username

    async def login(self, data: LoginSchema) -> str:
        logger.info("login_attempt username=%s", data.username)
        async with UnitOfWork(self._session_factory) as uow:
            user = await uow.users.get_by_username(data.username)
            if user is None or not user.is_active:
                logger.warning(
                    "login_failed username=%s reason=%s",
                    data.username,
                    "no_user_or_inactive",
                )
                raise InvalidCredentialsError
            if not await self._hasher.verify(user.hashed_password, data.password):
                logger.warning(
                    "login_failed username=%s reason=%s",
                    data.username,
                    "bad_password",
                )
                raise InvalidCredentialsError
            user_id = user.pk
            username = user.username
            is_admin = user.is_admin
        sid = await self._sessions.create(user_id, username, is_admin=is_admin)
        logger.info(
            "login_ok user_id=%d username=%s is_admin=%s",
            user_id,
            username,
            is_admin,
        )
        return self._signer.sign(sid)

    async def logout(self, signed_sid: str) -> None:
        sid = self._signer.unsign(signed_sid)
        if sid:
            await self._sessions.delete(sid)
            logger.info("logout_ok")
        else:
            logger.debug("logout_invalid_signature")

    async def logout_all(self, user_id: int) -> None:
        await self._sessions.delete_all_for_user(user_id)
        logger.info("logout_all user_id=%d", user_id)

    async def resolve_session(self, signed_sid: str | None) -> dict[str, object] | None:
        if not signed_sid:
            return None
        sid = self._signer.unsign(signed_sid)
        if not sid:
            logger.debug("session_unsign_failed")
            return None
        payload = await self._sessions.get(sid)
        if payload is None:
            logger.debug("session_payload_missing")
        return payload
