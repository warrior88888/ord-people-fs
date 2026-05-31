from __future__ import annotations

import pytest

from ord_people.exceptions import TagAlreadyExistsError
from ord_people.schemas.tag import TagCreateSchema


async def test_list_empty(tag_service):
    assert await tag_service.list_all() == []


async def test_create_then_list(tag_service):
    res = await tag_service.create(TagCreateSchema(name="music"))
    assert res.name == "music"
    assert [t.name for t in await tag_service.list_all()] == ["music"]


async def test_create_duplicate(tag_service):
    await tag_service.create(TagCreateSchema(name="music"))
    with pytest.raises(TagAlreadyExistsError):
        await tag_service.create(TagCreateSchema(name="music"))


async def test_list_sorted(tag_service):
    await tag_service.create(TagCreateSchema(name="zz"))
    await tag_service.create(TagCreateSchema(name="aa"))
    names = [t.name for t in await tag_service.list_all()]
    assert names == ["aa", "zz"]
