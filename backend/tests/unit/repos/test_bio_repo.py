from __future__ import annotations

from ord_people.repos.bio import BioRepo


async def test_get_missing(db_session, user_factory):
    u = await user_factory()
    assert await BioRepo(db_session).get_by_user(u.pk) is None


async def test_upsert_creates(db_session, user_factory):
    u = await user_factory()
    repo = BioRepo(db_session)
    bio = await repo.upsert(u.pk, about="hello")
    await db_session.commit()
    assert bio.about == "hello"
    fetched = await repo.get_by_user(u.pk)
    assert fetched is not None
    assert fetched.about == "hello"


async def test_upsert_updates(db_session, user_factory, bio_factory):
    u = await user_factory()
    await bio_factory(user_id=u.pk, about="old")
    repo = BioRepo(db_session)
    await repo.upsert(u.pk, about="new")
    await db_session.commit()
    fetched = await repo.get_by_user(u.pk)
    assert fetched is not None
    assert fetched.about == "new"


async def test_delete_for_user(db_session, user_factory, bio_factory):
    u = await user_factory()
    await bio_factory(user_id=u.pk)
    repo = BioRepo(db_session)
    await repo.delete_for_user(u.pk)
    await db_session.commit()
    assert await repo.get_by_user(u.pk) is None


async def test_delete_missing_is_noop(db_session, user_factory):
    u = await user_factory()
    await BioRepo(db_session).delete_for_user(u.pk)
