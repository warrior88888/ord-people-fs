from __future__ import annotations

import pytest_asyncio

from tests.factories._base import make_async_factory
from tests.factories.bio import BioFactory
from tests.factories.comment import CommentFactory
from tests.factories.post import PostFactory
from tests.factories.reaction import ReactionFactory
from tests.factories.tag import TagFactory
from tests.factories.user import UserFactory


@pytest_asyncio.fixture
async def user_factory(session_factory):
    return make_async_factory(UserFactory, session_factory)


@pytest_asyncio.fixture
async def tag_factory(session_factory):
    return make_async_factory(TagFactory, session_factory)


@pytest_asyncio.fixture
async def post_factory(session_factory, user_factory):
    create = make_async_factory(PostFactory, session_factory)

    async def _create(**overrides):
        if "author_id" not in overrides:
            author = await user_factory()
            overrides["author_id"] = author.pk
        return await create(**overrides)

    return _create


@pytest_asyncio.fixture
async def comment_factory(session_factory, user_factory, post_factory):
    create = make_async_factory(CommentFactory, session_factory)

    async def _create(**overrides):
        if "author_id" not in overrides:
            overrides["author_id"] = (await user_factory()).pk
        if "post_id" not in overrides:
            overrides["post_id"] = (await post_factory()).pk
        return await create(**overrides)

    return _create


@pytest_asyncio.fixture
async def reaction_factory(session_factory, user_factory, post_factory):
    create = make_async_factory(ReactionFactory, session_factory)

    async def _create(**overrides):
        if "user_id" not in overrides:
            overrides["user_id"] = (await user_factory()).pk
        if "post_id" not in overrides:
            overrides["post_id"] = (await post_factory()).pk
        return await create(**overrides)

    return _create


@pytest_asyncio.fixture
async def bio_factory(session_factory, user_factory):
    create = make_async_factory(BioFactory, session_factory)

    async def _create(**overrides):
        if "user_id" not in overrides:
            overrides["user_id"] = (await user_factory()).pk
        return await create(**overrides)

    return _create
