from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

import factory
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


def make_async_factory(
    factory_cls: type[factory.Factory],
    session_factory: async_sessionmaker[AsyncSession],
) -> Callable[..., Awaitable[Any]]:
    async def _create(**overrides: Any) -> Any:
        instance = factory_cls.build(**overrides)
        async with session_factory() as session:
            session.add(instance)
            await session.commit()
            await session.refresh(instance)
            return instance

    return _create
