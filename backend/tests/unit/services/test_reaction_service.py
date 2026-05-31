from __future__ import annotations

import pytest

from ord_people.exceptions import PostNotFoundError
from ord_people.utils.enums import ReactionType


async def test_post_404(reaction_service):
    with pytest.raises(PostNotFoundError):
        await reaction_service.toggle(99999, 1, ReactionType.LIKE)


async def test_add(reaction_service, post_factory, user_factory):
    p = await post_factory()
    u = await user_factory()
    counts, my = await reaction_service.toggle(p.pk, u.pk, ReactionType.LIKE)
    assert counts.like == 1
    assert my == ReactionType.LIKE


async def test_replace(reaction_service, post_factory, user_factory):
    p = await post_factory()
    u = await user_factory()
    await reaction_service.toggle(p.pk, u.pk, ReactionType.LIKE)
    counts, my = await reaction_service.toggle(p.pk, u.pk, ReactionType.SUPPORT)
    assert counts.like == 0
    assert counts.support == 1
    assert my == ReactionType.SUPPORT


async def test_toggle_off(reaction_service, post_factory, user_factory):
    p = await post_factory()
    u = await user_factory()
    await reaction_service.toggle(p.pk, u.pk, ReactionType.LIKE)
    counts, my = await reaction_service.toggle(p.pk, u.pk, ReactionType.LIKE)
    assert counts.like == 0
    assert my is None
