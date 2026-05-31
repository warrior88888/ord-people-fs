from __future__ import annotations

import pytest

from ord_people.exceptions import (
    CommentNotFoundError,
    ForbiddenError,
    PostNotFoundError,
)
from ord_people.schemas.comment import CommentCreateSchema, CommentUpdateSchema


async def test_list_post_404(comment_service):
    with pytest.raises(PostNotFoundError):
        await comment_service.list_by_post(99999, limit=10, offset=0)


async def test_create_post_404(comment_service):
    with pytest.raises(PostNotFoundError):
        await comment_service.create(99999, 1, CommentCreateSchema(text="hi"))


async def test_create_happy(comment_service, post_factory, user_factory):
    p = await post_factory()
    u = await user_factory()
    res = await comment_service.create(p.pk, u.pk, CommentCreateSchema(text="hi"))
    assert res.text == "hi"


async def test_update_not_found(comment_service):
    with pytest.raises(CommentNotFoundError):
        await comment_service.update(1, 99999, 1, CommentUpdateSchema(text="xy"))


async def test_update_post_mismatch(comment_service, comment_factory, post_factory):
    c = await comment_factory()
    other = await post_factory()
    with pytest.raises(CommentNotFoundError):
        await comment_service.update(
            other.pk, c.pk, c.author_id, CommentUpdateSchema(text="hijack")
        )


async def test_update_forbidden(comment_service, comment_factory, user_factory):
    c = await comment_factory()
    other = await user_factory()
    with pytest.raises(ForbiddenError):
        await comment_service.update(
            c.post_id, c.pk, other.pk, CommentUpdateSchema(text="hijack")
        )


async def test_delete_not_found(comment_service):
    with pytest.raises(CommentNotFoundError):
        await comment_service.delete(1, 99999, 1, False)


async def test_delete_forbidden(comment_service, comment_factory, user_factory):
    c = await comment_factory()
    other = await user_factory()
    with pytest.raises(ForbiddenError):
        await comment_service.delete(c.post_id, c.pk, other.pk, False)


async def test_delete_admin_ok(comment_service, comment_factory, user_factory):
    c = await comment_factory()
    admin = await user_factory(is_admin=True)
    await comment_service.delete(c.post_id, c.pk, admin.pk, True)
