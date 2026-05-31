from __future__ import annotations

import asyncio

from ord_people.models.comment import Comment
from ord_people.repos.comment import CommentRepo


async def test_create_and_get(db_session, post_factory, user_factory):
    post = await post_factory()
    user = await user_factory()
    repo = CommentRepo(db_session)
    c = await repo.create(post_id=post.pk, author_id=user.pk, text="hi")
    await db_session.commit()
    fetched = await repo.get_by_id(c.pk)
    assert fetched is not None
    assert fetched.text == "hi"


async def test_update(db_session, comment_factory):
    c = await comment_factory()
    repo = CommentRepo(db_session)
    fresh = await db_session.get(Comment, c.pk)
    await repo.update(fresh, text="updated")
    await db_session.commit()
    again = await db_session.get(Comment, c.pk)
    assert again.text == "updated"


async def test_delete(db_session, comment_factory):
    c = await comment_factory()
    repo = CommentRepo(db_session)
    fresh = await db_session.get(Comment, c.pk)
    await repo.delete(fresh)
    await db_session.commit()
    assert await db_session.get(Comment, c.pk) is None


async def test_list_and_count(db_session, post_factory, comment_factory):
    p = await post_factory()
    for _ in range(4):
        await comment_factory(post_id=p.pk)
        await asyncio.sleep(0.001)
    repo = CommentRepo(db_session)
    assert await repo.count_by_post(p.pk) == 4
    page = await repo.list_by_post(p.pk, limit=2, offset=0)
    assert len(page) == 2


async def test_list_other_post_empty(db_session, post_factory):
    p1 = await post_factory()
    p2 = await post_factory()
    repo = CommentRepo(db_session)
    assert await repo.list_by_post(p1.pk, limit=10, offset=0) == []
    assert await repo.count_by_post(p2.pk) == 0
