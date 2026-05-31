from __future__ import annotations

from ord_people.repos.reaction import ReactionRepo
from ord_people.utils.enums import ReactionType


async def test_set_and_get(db_session, post_factory, user_factory):
    p = await post_factory()
    u = await user_factory()
    repo = ReactionRepo(db_session)
    await repo.set(p.pk, u.pk, ReactionType.LIKE)
    await db_session.commit()
    got = await repo.get(p.pk, u.pk)
    assert got is not None
    assert got.reaction == ReactionType.LIKE


async def test_replace(db_session, post_factory, user_factory):
    p = await post_factory()
    u = await user_factory()
    repo = ReactionRepo(db_session)
    await repo.set(p.pk, u.pk, ReactionType.LIKE)
    await repo.set(p.pk, u.pk, ReactionType.SUPPORT)
    await db_session.commit()
    got = await repo.get(p.pk, u.pk)
    assert got is not None
    assert got.reaction == ReactionType.SUPPORT


async def test_delete(db_session, post_factory, user_factory):
    p = await post_factory()
    u = await user_factory()
    repo = ReactionRepo(db_session)
    await repo.set(p.pk, u.pk, ReactionType.LIKE)
    await repo.delete(p.pk, u.pk)
    await db_session.commit()
    assert await repo.get(p.pk, u.pk) is None


async def test_counts(db_session, post_factory, user_factory):
    p = await post_factory()
    u1 = await user_factory()
    u2 = await user_factory()
    u3 = await user_factory()
    repo = ReactionRepo(db_session)
    await repo.set(p.pk, u1.pk, ReactionType.LIKE)
    await repo.set(p.pk, u2.pk, ReactionType.LIKE)
    await repo.set(p.pk, u3.pk, ReactionType.SUPPORT)
    await db_session.commit()
    counts = await repo.counts_for_post(p.pk)
    assert counts[ReactionType.LIKE] == 2
    assert counts[ReactionType.SUPPORT] == 1


async def test_counts_empty(db_session, post_factory):
    p = await post_factory()
    counts = await ReactionRepo(db_session).counts_for_post(p.pk)
    assert counts == {}
