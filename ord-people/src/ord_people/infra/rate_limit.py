from __future__ import annotations

import logging
import secrets
from time import time
from typing import Annotated, Any, cast

import redis.asyncio as redis
from fastapi import Depends, HTTPException, Request, status

logger = logging.getLogger(__name__)


_LUA_SLIDING_WINDOW = """
redis.call("ZREMRANGEBYSCORE", KEYS[1], 0, ARGV[2])
local count = redis.call("ZCARD", KEYS[1])
if count >= tonumber(ARGV[3]) then
    return 1
end
redis.call("ZADD", KEYS[1], ARGV[1], ARGV[5])
if count == 0 then
    redis.call("EXPIRE", KEYS[1], ARGV[4])
end
return 0
"""


class RateLimiter:
    """Sliding-window rate limiter backed by Redis sorted sets + atomic Lua.

    Fail-OPEN by design: if Redis is unreachable or the script errors out,
    requests are allowed through. The product requirement is that the demo
    must keep serving traffic even if the limiter back-end is down.
    """

    def __init__(self, redis_client: redis.Redis) -> None:
        self._redis = redis_client
        self._sha: str | None = None

    @staticmethod
    def client_ip(request: Request) -> str:
        # ProxyHeadersMiddleware (when behind_proxy) already rewrites
        # request.client.host from a trusted X-Forwarded-For — no need
        # to re-parse the header here and risk trusting a spoofed value.
        return request.client.host if request.client else "unknown"

    async def _ensure_script(self) -> str:
        if self._sha is None:
            self._sha = await self._redis.script_load(_LUA_SLIDING_WINDOW)
            logger.debug("rate_limit_script_loaded sha=%s", self._sha)
        return self._sha

    async def is_limited(
        self,
        ip: str,
        endpoint: str,
        max_requests: int,
        window_seconds: int,
    ) -> bool:
        key = f"rate_limiter:{endpoint}:{ip}"
        now_ms = int(time() * 1000)
        window_start_ms = now_ms - window_seconds * 1000
        member = f"{now_ms}-{secrets.token_hex(8)}"

        args: tuple[Any, ...] = (
            1,
            key,
            now_ms,
            window_start_ms,
            max_requests,
            window_seconds,
            member,
        )
        try:
            sha = await self._ensure_script()
            raw = await cast(Any, self._redis.evalsha(sha, *args))
        except redis.ResponseError:
            logger.warning("rate_limit_script_evict endpoint=%s ip=%s", endpoint, ip)
            self._sha = None
            try:
                raw = await cast(Any, self._redis.eval(_LUA_SLIDING_WINDOW, *args))
            except Exception:
                logger.exception(
                    "rate_limit_eval_failed endpoint=%s ip=%s", endpoint, ip
                )
                return False  # fail-OPEN
        except Exception:
            logger.exception("rate_limit_failed endpoint=%s ip=%s", endpoint, ip)
            return False  # fail-OPEN

        is_blocked = int(raw) == 1
        if is_blocked:
            logger.info(
                "rate_limit_blocked endpoint=%s ip=%s max=%d window_s=%d",
                endpoint,
                ip,
                max_requests,
                window_seconds,
            )
        else:
            logger.debug("rate_limit_allowed endpoint=%s ip=%s", endpoint, ip)
        return is_blocked


def get_rate_limiter(request: Request) -> RateLimiter:
    return request.app.state.rate_limiter


def rate_limit(endpoint: str, max_requests: int, window_seconds: int):
    """Build a FastAPI dependency that enforces a per-endpoint sliding-window limit."""

    async def dependency(
        request: Request,
        limiter: Annotated[RateLimiter, Depends(get_rate_limiter)],
    ) -> None:
        ip = limiter.client_ip(request)
        if await limiter.is_limited(ip, endpoint, max_requests, window_seconds):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests, please retry later",
                headers={"Retry-After": str(window_seconds)},
            )

    return dependency
