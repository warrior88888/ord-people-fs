from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import redis.asyncio as redis

logger = logging.getLogger(__name__)


class RedisCache:
    def __init__(self, client: redis.Redis) -> None:
        self._client = client

    @property
    def client(self) -> redis.Redis:
        return self._client

    async def get(self, key: str) -> str | None:
        value = await self._client.get(key)
        if value is None:
            logger.debug("cache_get_miss key=%s", key)
            return None
        logger.debug("cache_get_hit key=%s", key)
        return value.decode() if isinstance(value, bytes) else value

    async def setex(self, key: str, ttl: int, value: str) -> None:
        await self._client.setex(key, ttl, value)
        logger.debug("cache_setex key=%s ttl=%d bytes=%d", key, ttl, len(value))

    async def delete(self, *keys: str) -> None:
        if keys:
            await self._client.delete(*keys)
            logger.debug("cache_delete keys=%s", list(keys))

    async def incr(self, key: str) -> int:
        new_value = int(await self._client.incr(key))
        logger.debug("cache_incr key=%s new=%d", key, new_value)
        return new_value

    async def close(self) -> None:
        await self._client.aclose()
        logger.info("redis_cache_closed")
