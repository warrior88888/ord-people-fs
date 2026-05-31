from __future__ import annotations


async def test_first_request_allowed(rate_limiter):
    assert await rate_limiter.is_limited("1.1.1.1", "ep", 2, 60) is False


async def test_under_limit_allows(rate_limiter):
    for _ in range(3):
        assert await rate_limiter.is_limited("1.1.1.1", "ep", 5, 60) is False


async def test_over_limit_blocks(rate_limiter):
    for _ in range(2):
        await rate_limiter.is_limited("1.1.1.1", "ep", 2, 60)
    assert await rate_limiter.is_limited("1.1.1.1", "ep", 2, 60) is True


async def test_distinct_ips_independent(rate_limiter):
    for _ in range(2):
        await rate_limiter.is_limited("1.1.1.1", "ep", 2, 60)
    assert await rate_limiter.is_limited("2.2.2.2", "ep", 2, 60) is False


async def test_distinct_endpoints_independent(rate_limiter):
    for _ in range(2):
        await rate_limiter.is_limited("1.1.1.1", "ep1", 2, 60)
    assert await rate_limiter.is_limited("1.1.1.1", "ep2", 2, 60) is False
