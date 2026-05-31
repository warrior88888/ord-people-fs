from __future__ import annotations

import datetime

from ord_people.models.user import User
from ord_people.repos.user import UserRepo


async def test_create_then_get_by_id(db_session):
    repo = UserRepo(db_session)
    u = await repo.create(
        username="u1", hashed_password="h", first_name="F", last_name="L"
    )
    await db_session.commit()
    fetched = await repo.get_by_id(u.pk)
    assert fetched is not None
    assert fetched.username == "u1"


async def test_get_by_username_with_bio(db_session, bio_factory, user_factory):
    user = await user_factory(username="bioguy")
    await bio_factory(user_id=user.pk, about="hello")
    fresh = await UserRepo(db_session).get_by_username("bioguy", with_bio=True)
    assert fresh is not None
    assert fresh.bio is not None
    assert fresh.bio.about == "hello"


async def test_get_by_username_excludes_soft_deleted(db_session, user_factory):
    user = await user_factory(username="ghosty")
    async with db_session.bind.begin() as conn:
        await conn.run_sync(lambda _: None)
    user_db = await db_session.get(User, user.pk)
    user_db.deleted_at = datetime.datetime.now(datetime.UTC)
    await db_session.commit()
    assert await UserRepo(db_session).get_by_username("ghosty") is None


async def test_exists_by_username(db_session, user_factory):
    await user_factory(username="present")
    repo = UserRepo(db_session)
    assert await repo.exists_by_username("present") is True
    assert await repo.exists_by_username("absent") is False


async def test_update_skips_none(db_session, user_factory):
    user = await user_factory(first_name="Old")
    repo = UserRepo(db_session)
    fresh = await db_session.get(User, user.pk)
    await repo.update(fresh, first_name=None, last_name="NewLast")
    await db_session.commit()
    again = await db_session.get(User, user.pk)
    assert again.first_name == "Old"
    assert again.last_name == "NewLast"


async def test_set_avatar(db_session, user_factory):
    user = await user_factory()
    repo = UserRepo(db_session)
    fresh = await db_session.get(User, user.pk)
    await repo.set_avatar(fresh, "k/1")
    await db_session.commit()
    again = await db_session.get(User, user.pk)
    assert again.avatar_key == "k/1"
    await repo.set_avatar(again, None)
    await db_session.commit()
    again = await db_session.get(User, user.pk)
    assert again.avatar_key is None


async def test_list_and_count_feed(db_session, user_factory):
    for _ in range(3):
        await user_factory()
    await user_factory(is_active=False)
    repo = UserRepo(db_session)
    feed = await repo.list_feed(limit=10, offset=0)
    count = await repo.count_feed()
    assert len(feed) == 3
    assert count == 3


async def test_feed_pagination(db_session, user_factory):
    for _ in range(5):
        await user_factory()
    repo = UserRepo(db_session)
    page1 = await repo.list_feed(limit=2, offset=0)
    page2 = await repo.list_feed(limit=2, offset=2)
    assert len(page1) == 2
    assert len(page2) == 2
    assert {u.pk for u in page1}.isdisjoint({u.pk for u in page2})
