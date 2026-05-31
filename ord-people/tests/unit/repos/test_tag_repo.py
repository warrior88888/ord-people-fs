from __future__ import annotations

import pytest
from sqlalchemy.exc import IntegrityError

from ord_people.repos.tag import TagRepo


async def test_create_and_get(db_session):
    repo = TagRepo(db_session)
    t = await repo.create("alpha")
    await db_session.commit()
    fetched = await repo.get_by_id(t.pk)
    assert fetched is not None
    assert fetched.name == "alpha"


async def test_duplicate_raises(db_session):
    repo = TagRepo(db_session)
    await repo.create("alpha")
    await db_session.commit()
    with pytest.raises(IntegrityError):
        await repo.create("alpha")


async def test_list_all_sorted(db_session, tag_factory):
    await tag_factory(name="zebra")
    await tag_factory(name="alpha")
    await tag_factory(name="middle")
    names = [t.name for t in await TagRepo(db_session).list_all()]
    assert names == ["alpha", "middle", "zebra"]


async def test_list_by_ids(db_session, tag_factory):
    t1 = await tag_factory()
    t2 = await tag_factory()
    await tag_factory()
    found = await TagRepo(db_session).list_by_ids([t1.pk, t2.pk])
    assert {t.pk for t in found} == {t1.pk, t2.pk}


async def test_list_by_ids_empty(db_session):
    assert await TagRepo(db_session).list_by_ids([]) == []
