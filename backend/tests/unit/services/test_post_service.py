from __future__ import annotations

import pytest

from ord_people.db.uow import UnitOfWork
from ord_people.exceptions import (
    ForbiddenError,
    PostNotFoundError,
    UserNotFoundError,
)
from ord_people.schemas.post import (
    PostCreateSchema,
    PostFeedFilters,
    PostUpdateSchema,
)
from ord_people.services.post import _PostCachePayload
from ord_people.utils.enums import PostCategory, ReactionType


def _create(name="Hello", tag_ids=None):
    return PostCreateSchema(
        name=name,
        description="An ok description.",
        category=PostCategory.STORY,
        external_url=None,
        tag_ids=tag_ids or [],
    )


async def test_create_unknown_author(post_service):
    with pytest.raises(UserNotFoundError):
        await post_service.create(99999, _create())


async def test_create_happy(post_service, user_factory):
    u = await user_factory()
    res = await post_service.create(u.pk, _create())
    assert res.pk > 0
    assert res.author.pk == u.pk


async def test_get_unknown(post_service):
    with pytest.raises(PostNotFoundError):
        await post_service.get(99999, current_user_id=None)


async def test_get_cached_path(post_service, post_factory):
    p = await post_factory()
    a = await post_service.get(p.pk, current_user_id=None)
    b = await post_service.get(p.pk, current_user_id=None)
    assert a.pk == b.pk


async def test_update_not_found(post_service):
    with pytest.raises(PostNotFoundError):
        await post_service.update(99999, 1, PostUpdateSchema(name="Hello"))


async def test_update_forbidden(post_service, post_factory, user_factory):
    other = await user_factory()
    p = await post_factory()
    with pytest.raises(ForbiddenError):
        await post_service.update(p.pk, other.pk, PostUpdateSchema(name="hijack"))


async def test_delete_not_found(post_service):
    with pytest.raises(PostNotFoundError):
        await post_service.delete(99999, 1, False)


async def test_delete_forbidden(post_service, post_factory, user_factory):
    other = await user_factory()
    p = await post_factory()
    with pytest.raises(ForbiddenError):
        await post_service.delete(p.pk, other.pk, False)


async def test_delete_admin_ok(post_service, post_factory, user_factory):
    other = await user_factory()
    p = await post_factory()
    await post_service.delete(p.pk, other.pk, True)


async def test_list_feed_uncached_path(post_service, post_factory):
    await post_factory()
    res = await post_service.list_feed(
        limit=10,
        offset=0,
        filters=PostFeedFilters(category=PostCategory.STORY),
    )
    assert res.total == 1


async def test_list_feed_cached_path(post_service, post_factory):
    await post_factory()
    a = await post_service.list_feed(limit=10, offset=0, filters=PostFeedFilters())
    b = await post_service.list_feed(limit=10, offset=0, filters=PostFeedFilters())
    assert a.total == b.total == 1


async def test_upload_photo_not_found(post_service):
    with pytest.raises(PostNotFoundError):
        await post_service.upload_photo(99999, 1, b"x")


async def test_upload_photo_forbidden(post_service, post_factory, user_factory):
    other = await user_factory()
    p = await post_factory()
    with pytest.raises(ForbiddenError):
        await post_service.upload_photo(p.pk, other.pk, b"x")


async def test_upload_photo_happy(post_service, post_factory, storage):
    p = await post_factory()
    url = await post_service.upload_photo(p.pk, p.author_id, b"x")
    assert url.startswith("https://fake.cdn/")
    assert len(storage.objects) == 1


async def test_get_cache_payload_has_no_author(post_service, post_factory, cache):
    p = await post_factory()
    await post_service.get(p.pk, current_user_id=None)
    raw = await cache.get(f"post:{p.pk}")
    assert raw is not None
    payload = _PostCachePayload.model_validate_json(raw)
    assert payload.author_id == p.author_id
    assert '"author":' not in raw
    assert "my_reaction" not in raw


async def test_get_cache_hit_hydrates_fresh_author(
    post_service, post_factory, session_factory, cache
):
    p = await post_factory()
    first = await post_service.get(p.pk, current_user_id=None)
    assert await cache.get(f"post:{p.pk}") is not None
    async with UnitOfWork(session_factory) as uow:
        author = await uow.users.get_by_id(p.author_id)
        await uow.users.update(author, first_name="Renamed", last_name="Author")  # ty: ignore [invalid-argument-type]

    second = await post_service.get(p.pk, current_user_id=None)
    assert second.pk == first.pk
    assert second.author.first_name == "Renamed"
    assert second.author.last_name == "Author"


async def test_get_cache_hit_my_reaction_is_per_user(
    post_service, reaction_service, post_factory, user_factory
):
    p = await post_factory()
    viewer_with_reaction = await user_factory()
    viewer_without = await user_factory()
    await reaction_service.toggle(p.pk, viewer_with_reaction.pk, ReactionType.LIKE)
    await post_service.get(p.pk, current_user_id=viewer_with_reaction.pk)
    a = await post_service.get(p.pk, current_user_id=viewer_with_reaction.pk)
    b = await post_service.get(p.pk, current_user_id=viewer_without.pk)
    c = await post_service.get(p.pk, current_user_id=None)
    assert a.my_reaction == ReactionType.LIKE
    assert b.my_reaction is None
    assert c.my_reaction is None


async def test_get_cache_hit_with_missing_author_falls_back(
    post_service, post_factory, cache
):
    p = await post_factory()
    stale = _PostCachePayload(
        pk=p.pk,
        name=p.name,
        description=p.description,
        category=p.category,
        photo_url=None,
        external_url=None,
        author_id=999_999,
        tags=[],
        reactions=(await post_service.get(p.pk, current_user_id=None)).reactions,
        created_at=p.created_at,
        updated_at=p.updated_at,
    )
    await cache.setex(f"post:{p.pk}", 60, stale.model_dump_json())
    res = await post_service.get(p.pk, current_user_id=None)
    assert res.author.pk == p.author_id
