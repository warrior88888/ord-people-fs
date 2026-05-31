from __future__ import annotations

import datetime

from ord_people.models.post import Post
from ord_people.repos.post import PostRepo
from ord_people.utils.enums import PostCategory


async def test_create_with_tags(db_session, user_factory, tag_factory):
    u = await user_factory()
    t1 = await tag_factory()
    t2 = await tag_factory()
    fresh_t1 = await db_session.get(type(t1), t1.pk)
    fresh_t2 = await db_session.get(type(t2), t2.pk)
    repo = PostRepo(db_session)
    p = await repo.create(
        author_id=u.pk,
        name="Hi",
        description="A nice text",
        category=PostCategory.STORY,
        external_url=None,
        tags=[fresh_t1, fresh_t2],
    )
    await db_session.commit()
    fresh = await repo.get_by_id(p.pk)
    assert fresh is not None
    assert {t.pk for t in fresh.tags} == {t1.pk, t2.pk}


async def test_get_by_id_not_found(db_session):
    assert await PostRepo(db_session).get_by_id(9999) is None


async def test_update_replaces_tags(db_session, user_factory, tag_factory):
    u = await user_factory()
    t1 = await tag_factory()
    t2 = await tag_factory()
    repo = PostRepo(db_session)
    p = await repo.create(
        author_id=u.pk,
        name="x",
        description="ok ok ok ok",
        category=PostCategory.STORY,
        external_url=None,
        tags=[await db_session.get(type(t1), t1.pk)],
    )
    await db_session.commit()
    fresh = await repo.get_by_id(p.pk)
    assert fresh is not None
    await repo.update(fresh, tags=[await db_session.get(type(t2), t2.pk)], name="x2")
    await db_session.commit()
    again = await repo.get_by_id(p.pk)
    assert again is not None
    assert {t.pk for t in again.tags} == {t2.pk}
    assert again.name == "x2"


async def test_delete(db_session, post_factory):
    p = await post_factory()
    repo = PostRepo(db_session)
    fresh = await db_session.get(Post, p.pk)
    await repo.delete(fresh)
    await db_session.commit()
    assert await db_session.get(Post, p.pk) is None


async def test_set_photo(db_session, post_factory):
    p = await post_factory()
    repo = PostRepo(db_session)
    fresh = await db_session.get(Post, p.pk)
    await repo.set_photo(fresh, "ph/1")
    await db_session.commit()
    again = await db_session.get(Post, p.pk)
    assert again.photo_key == "ph/1"


async def test_feed_filter_author(db_session, user_factory, post_factory):
    u1 = await user_factory()
    u2 = await user_factory()
    await post_factory(author_id=u1.pk)
    await post_factory(author_id=u2.pk)
    repo = PostRepo(db_session)
    feed = await repo.list_feed(limit=10, offset=0, author_id=u1.pk)
    assert len(feed) == 1
    assert feed[0].author_id == u1.pk


async def test_feed_filter_category(db_session, post_factory):
    await post_factory(category=PostCategory.STORY)
    await post_factory(category=PostCategory.NEWS)
    repo = PostRepo(db_session)
    feed = await repo.list_feed(limit=10, offset=0, category=PostCategory.NEWS)
    assert len(feed) == 1


async def test_feed_filter_date_range(db_session, post_factory):
    await post_factory()
    await post_factory()
    now = datetime.datetime.now(datetime.UTC)
    repo = PostRepo(db_session)
    feed = await repo.list_feed(
        limit=10, offset=0, date_from=now + datetime.timedelta(hours=1)
    )
    assert feed == []


async def test_count_with_and_without_tags(
    db_session, user_factory, tag_factory, post_factory
):
    u = await user_factory()
    t = await tag_factory()
    p = await post_factory(author_id=u.pk)
    from ord_people.models.tag import post_tags

    await db_session.execute(
        post_tags.insert(), [{"post_id": p.pk, "tag_id": t.pk}]
    )
    await db_session.commit()
    repo = PostRepo(db_session)
    assert await repo.count_feed(tag_ids=[t.pk]) == 1
    assert await repo.count_feed() == 1
