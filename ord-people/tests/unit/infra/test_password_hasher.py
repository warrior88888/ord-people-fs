from __future__ import annotations

import pytest

from ord_people.infra.auth.password_hasher import Argon2PasswordHasher


async def test_hash_then_verify_true(hasher: Argon2PasswordHasher):
    h = await hasher.hash("MySecret123!")
    assert await hasher.verify(h, "MySecret123!") is True


async def test_verify_wrong_password_false(hasher):
    h = await hasher.hash("MySecret123!")
    assert await hasher.verify(h, "WrongOne!!1") is False


async def test_hashes_differ_for_same_password(hasher):
    a = await hasher.hash("MySecret123!")
    b = await hasher.hash("MySecret123!")
    assert a != b


async def test_pepper_changes_hash():
    a = Argon2PasswordHasher(pepper="p1", time_cost=1, memory_cost=8192)
    b = Argon2PasswordHasher(pepper="p2", time_cost=1, memory_cost=8192)
    ha = await a.hash("Xx")
    assert await b.verify(ha, "Xx") is False


@pytest.mark.parametrize("bogus", ["", "not-a-hash", "$argon2id$broken"])
async def test_verify_garbage_raises(hasher, bogus):
    # The production verifier only catches VerifyMismatchError; unparseable
    # hashes propagate as argon2.exceptions.InvalidHashError /
    # VerificationError. Documenting the contract here.
    from argon2.exceptions import InvalidHashError, VerificationError

    with pytest.raises((VerificationError, InvalidHashError)):
        await hasher.verify(bogus, "anything")


async def test_empty_password_hashable(hasher):
    h = await hasher.hash("")
    assert await hasher.verify(h, "") is True
    assert await hasher.verify(h, "x") is False
