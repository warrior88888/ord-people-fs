from __future__ import annotations

import json
import logging
import secrets
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    import redis.asyncio as redis

logger = logging.getLogger(__name__)


class RedisSessionRepository:
    def __init__(self, client: redis.Redis, ttl: int) -> None:
        self._client = client
        self._ttl = ttl

    @staticmethod
    def _sk(sid: str) -> str:
        return f"session:{sid}"

    @staticmethod
    def _uk(user_id: int) -> str:
        return f"user_sessions:{user_id}"

    async def create(
        self, user_id: int, username: str, *, is_admin: bool = False
    ) -> str:
        sid = secrets.token_urlsafe(32)
        payload = json.dumps(
            {"user_id": user_id, "username": username, "is_admin": is_admin},
        )
        async with self._client.pipeline(transaction=True) as pipe:
            # noinspection PyAsyncCall
            pipe.setex(self._sk(sid), self._ttl, payload)
            pipe.sadd(self._uk(user_id), sid)
            # noinspection PyAsyncCall
            pipe.expire(self._uk(user_id), self._ttl)
            await pipe.execute()
        logger.info(
            "session_created user_id=%d username=%s ttl=%d",
            user_id,
            username,
            self._ttl,
        )
        return sid

    async def get(self, sid: str) -> dict[str, object] | None:
        raw: bytes | None = await self._client.get(self._sk(sid))
        if raw is None:
            logger.debug("session_lookup_miss")
            return None
        return json.loads(raw)

    async def delete(self, sid: str) -> None:
        data = await self.get(sid)
        async with self._client.pipeline(transaction=True) as pipe:
            # noinspection PyAsyncCall
            pipe.delete(self._sk(sid))
            if data:
                pipe.srem(self._uk(int(cast(str, data["user_id"]))), sid)
            await pipe.execute()
        if data:
            logger.info("session_deleted user_id=%s", data.get("user_id"))
        else:
            logger.debug("session_delete_unknown_sid")

    async def delete_all_for_user(self, user_id: int) -> None:
        sids: set[bytes | str] = await self._client.smembers(self._uk(user_id))  # ty: ignore[invalid-await]
        decoded = [s.decode() if isinstance(s, bytes) else s for s in sids]
        async with self._client.pipeline(transaction=True) as pipe:
            for sid in decoded:
                # noinspection PyAsyncCall
                pipe.delete(self._sk(sid))
            # noinspection PyAsyncCall
            pipe.delete(self._uk(user_id))
            await pipe.execute()
        logger.info(
            "session_all_deleted user_id=%d sessions=%d", user_id, len(decoded)
        )
