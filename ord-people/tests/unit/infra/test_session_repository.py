from __future__ import annotations


async def test_create_then_get(session_repository):
    sid = await session_repository.create(1, "alice", is_admin=False)
    data = await session_repository.get(sid)
    assert data == {"user_id": 1, "username": "alice", "is_admin": False}


async def test_get_missing_returns_none(session_repository):
    assert await session_repository.get("nonexistent") is None


async def test_delete_removes(session_repository):
    sid = await session_repository.create(1, "alice")
    await session_repository.delete(sid)
    assert await session_repository.get(sid) is None


async def test_delete_unknown_is_noop(session_repository):
    await session_repository.delete("nope")


async def test_concurrent_creates_distinct_sids(session_repository):
    a = await session_repository.create(1, "alice")
    b = await session_repository.create(1, "alice")
    assert a != b
    assert await session_repository.get(a) is not None
    assert await session_repository.get(b) is not None


async def test_delete_all_for_user(session_repository):
    a = await session_repository.create(7, "u7")
    b = await session_repository.create(7, "u7")
    c = await session_repository.create(8, "u8")
    await session_repository.delete_all_for_user(7)
    assert await session_repository.get(a) is None
    assert await session_repository.get(b) is None
    assert await session_repository.get(c) is not None


async def test_is_admin_flag(session_repository):
    sid = await session_repository.create(2, "boss", is_admin=True)
    data = await session_repository.get(sid)
    assert data["is_admin"] is True


async def test_ttl_set(session_repository, redis_client):
    sid = await session_repository.create(1, "a")
    ttl = await redis_client.ttl(f"session:{sid}")
    assert ttl > 0
