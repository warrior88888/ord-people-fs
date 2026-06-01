from __future__ import annotations

import pytest

from ord_people.exceptions import InvalidCredentialsError, UsernameAlreadyTakenError
from ord_people.schemas.auth import LoginSchema, RegisterSchema


def _register(username="someone1", password="Sup3rSecret!"):
    return RegisterSchema(
        username=username,
        password=password,
        first_name="First",
        last_name="Last",
    )


async def test_register_happy(auth_service):
    user_id, username = await auth_service.register(_register())
    assert user_id > 0
    assert username == "someone1"


async def test_register_invalidates_users_feed_cache(
    auth_service, user_service, user_factory
):
    await user_factory(username="existing1")
    first = await user_service.list_feed(limit=10, offset=0)
    assert first.total == 1
    await auth_service.register(_register(username="freshone"))
    refreshed = await user_service.list_feed(limit=10, offset=0)
    assert refreshed.total == 2
    assert {u.username for u in refreshed.items} == {"existing1", "freshone"}


async def test_register_duplicate(auth_service, user_factory):
    await user_factory(username="someone1")
    with pytest.raises(UsernameAlreadyTakenError):
        await auth_service.register(_register())


async def test_login_unknown(auth_service):
    with pytest.raises(InvalidCredentialsError):
        await auth_service.login(
            LoginSchema(username="ghosty", password="Sup3rSecret!")
        )


async def test_login_inactive(auth_service, make_user):
    await make_user(username="inactiveone", is_active=False)
    with pytest.raises(InvalidCredentialsError):
        await auth_service.login(
            LoginSchema(username="inactiveone", password="Sup3rSecret!")
        )


async def test_login_wrong_password(auth_service, make_user):
    await make_user(username="bobby2")
    with pytest.raises(InvalidCredentialsError):
        await auth_service.login(
            LoginSchema(username="bobby2", password="WrongPassword!")
        )


async def test_login_and_resolve(auth_service, make_user):
    await make_user(username="bobby3")
    signed = await auth_service.login(
        LoginSchema(username="bobby3", password="Sup3rSecret!")
    )
    payload = await auth_service.resolve_session(signed)
    assert payload is not None
    assert payload["username"] == "bobby3"


async def test_resolve_none(auth_service):
    assert await auth_service.resolve_session(None) is None


async def test_resolve_bogus(auth_service):
    assert await auth_service.resolve_session("garbage.no.signature") is None


async def test_logout(auth_service, make_user):
    await make_user(username="bobby4")
    signed = await auth_service.login(
        LoginSchema(username="bobby4", password="Sup3rSecret!")
    )
    await auth_service.logout(signed)
    assert await auth_service.resolve_session(signed) is None


async def test_logout_all(auth_service, make_user):
    user = await make_user(username="bobby5")
    a = await auth_service.login(
        LoginSchema(username="bobby5", password="Sup3rSecret!")
    )
    b = await auth_service.login(
        LoginSchema(username="bobby5", password="Sup3rSecret!")
    )
    await auth_service.logout_all(user.pk)
    assert await auth_service.resolve_session(a) is None
    assert await auth_service.resolve_session(b) is None


async def test_logout_with_invalid_signature_is_noop(auth_service):
    await auth_service.logout("garbage")
