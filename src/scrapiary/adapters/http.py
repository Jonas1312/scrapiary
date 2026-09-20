from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable

import httpx2


class PerHostRequestThrottle:
    def __init__(
        self,
        interval_seconds: float,
        *,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        if interval_seconds < 0:
            raise ValueError("interval_seconds must not be negative")
        self._interval_seconds = interval_seconds
        self._clock = clock
        self._sleep = sleep
        self._locks: dict[str, asyncio.Lock] = {}
        self._last_started_at: dict[str, float] = {}

    async def __call__(self, request: httpx2.Request) -> None:
        host = request.url.host
        lock = self._locks.setdefault(host, asyncio.Lock())
        async with lock:
            last_started_at = self._last_started_at.get(host)
            if last_started_at is not None:
                wait = self._interval_seconds - (self._clock() - last_started_at)
                if wait > 0:
                    await self._sleep(wait)
            self._last_started_at[host] = self._clock()
