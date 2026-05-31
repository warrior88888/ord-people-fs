from __future__ import annotations


async def test_setex_then_get(cache):
    await cache.setex("k", 60, "hello")
    assert await cache.get("k") == "hello"


async def test_get_miss(cache):
    assert await cache.get("nope") is None


async def test_delete(cache):
    await cache.setex("k", 60, "v")
    await cache.delete("k")
    assert await cache.get("k") is None


async def test_delete_noop_on_missing(cache):
    await cache.delete("missing")


async def test_delete_no_keys_noop(cache):
    await cache.delete()


async def test_incr_starts_at_one(cache):
    assert await cache.incr("counter") == 1
    assert await cache.incr("counter") == 2


async def test_ttl_applied(cache, redis_client):
    await cache.setex("ttl-key", 30, "v")
    ttl = await redis_client.ttl("ttl-key")
    assert 0 < ttl <= 30
