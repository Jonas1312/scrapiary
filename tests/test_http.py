from __future__ import annotations

import httpx2

from scrapiary.adapters.http import PerHostRequestThrottle


async def test_request_throttle_spaces_requests_to_the_same_host() -> None:
    now = 100.0
    sleeps: list[float] = []

    def clock() -> float:
        return now

    async def sleep(seconds: float) -> None:
        nonlocal now
        sleeps.append(seconds)
        now += seconds

    throttle = PerHostRequestThrottle(interval_seconds=1.0, clock=clock, sleep=sleep)
    await throttle(httpx2.Request("GET", "https://example.com/first"))
    now += 0.25
    await throttle(httpx2.Request("GET", "https://example.com/second"))
    await throttle(httpx2.Request("GET", "https://another.example/first"))

    assert sleeps == [0.75]
