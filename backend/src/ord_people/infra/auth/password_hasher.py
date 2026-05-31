from __future__ import annotations

import asyncio
import logging

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

logger = logging.getLogger(__name__)


class Argon2PasswordHasher:
    def __init__(self, pepper: str, time_cost: int, memory_cost: int) -> None:
        self._pepper = pepper
        self._hasher = PasswordHasher(
            time_cost=time_cost,
            memory_cost=memory_cost,
            parallelism=2,
        )
        logger.debug(
            "argon2_hasher_initialized time_cost=%d memory_cost=%d parallelism=%d",
            time_cost,
            memory_cost,
            2,
        )

    def _peppered(self, password: str) -> str:
        return password + self._pepper

    async def hash(self, password: str) -> str:
        logger.debug("password_hash_start")
        result = await asyncio.get_running_loop().run_in_executor(
            None, self._hasher.hash, self._peppered(password)
        )
        logger.debug("password_hash_done")
        return result

    async def verify(self, hashed: str, password: str) -> bool:
        def _verify(h: str, p: str) -> bool:
            try:
                return self._hasher.verify(h, self._peppered(p))
            except VerifyMismatchError:
                return False

        ok = await asyncio.get_running_loop().run_in_executor(
            None, _verify, hashed, password
        )
        logger.debug("password_verify result=%s", ok)
        return ok
