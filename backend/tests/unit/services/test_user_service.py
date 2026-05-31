from __future__ import annotations

import pytest

from ord_people.config.constatns.media import IMAGE_INPUT_MAX_SIZE
from ord_people.exceptions import AvatarTooLargeError, UserNotFoundError
from ord_people.schemas.bio import BioUpdateSchema
from ord_people.schemas.user import UserUpdateSchema


async def test_list_feed_empty(user_service):
    res = await user_service.list_feed(limit=10, offset=0)
    assert res.items == []
    assert res.total == 0


async def test_list_feed_caches(user_service, user_factory):
    await user_factory()
    a = await user_service.list_feed(limit=10, offset=0)
    b = await user_service.list_feed(limit=10, offset=0)
    assert a.total == b.total == 1


async def test_get_by_username_404(user_service):
    with pytest.raises(UserNotFoundError):
        await user_service.get_by_username("nobody")


async def test_get_by_username_cached(user_service, user_factory):
    u = await user_factory(username="cached_one")
    first = await user_service.get_by_username("cached_one")
    second = await user_service.get_by_username("cached_one")
    assert first.pk == second.pk == u.pk


async def test_update_me_invalidates_cache(user_service, user_factory):
    u = await user_factory(username="updater1")
    await user_service.get_by_username("updater1")
    await user_service.update_me(u.pk, UserUpdateSchema(first_name="NewFirst"))
    refreshed = await user_service.get_by_username("updater1")
    assert refreshed.first_name == "NewFirst"


async def test_update_me_unknown(user_service):
    with pytest.raises(UserNotFoundError):
        await user_service.update_me(99999, UserUpdateSchema(first_name="Xx"))


async def test_update_bio_creates(user_service, user_factory):
    u = await user_factory()
    bio = await user_service.update_bio(u.pk, BioUpdateSchema(about="hi"))
    assert bio.about == "hi"


async def test_update_bio_unknown(user_service):
    with pytest.raises(UserNotFoundError):
        await user_service.update_bio(99999, BioUpdateSchema(about="x"))


async def test_upload_avatar_too_large(user_service, user_factory):
    u = await user_factory()
    with pytest.raises(AvatarTooLargeError):
        await user_service.upload_avatar(u.pk, b"\x00" * (IMAGE_INPUT_MAX_SIZE + 1))


async def test_upload_avatar_happy(user_service, user_factory, storage):
    u = await user_factory()
    url = await user_service.upload_avatar(u.pk, b"data")
    assert url.startswith("https://fake.cdn/")
    assert len(storage.objects) == 1


async def test_upload_avatar_replaces_old(user_service, user_factory, storage):
    u = await user_factory()
    await user_service.upload_avatar(u.pk, b"first")
    await user_service.upload_avatar(u.pk, b"second")
    assert len(storage.deletes) >= 1


async def test_upload_avatar_unknown_user(user_service):
    with pytest.raises(UserNotFoundError):
        await user_service.upload_avatar(99999, b"data")


async def test_delete_me_anonymizes(user_service, user_factory, db_session):
    u = await user_factory(username="todelete3")
    await user_service.delete_me(u.pk)
    from ord_people.models.user import User

    fresh = await db_session.get(User, u.pk)
    assert fresh.is_active is False
    assert fresh.deleted_at is not None
    assert fresh.username.startswith("deleted-")


async def test_delete_me_unknown(user_service):
    with pytest.raises(UserNotFoundError):
        await user_service.delete_me(99999)
