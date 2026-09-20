from __future__ import annotations

import httpx2

from scrapiary.adapters.filesystem import JsonStateRepository, RssFeedPublisher
from scrapiary.adapters.http import PerHostRequestThrottle
from scrapiary.application import FeedRefresher, ScraperHealthChecker
from scrapiary.config import Settings
from scrapiary.registry import build_scrapers


def build_refresher(client: httpx2.AsyncClient, settings: Settings) -> FeedRefresher:
    return FeedRefresher(
        build_scrapers(client),
        JsonStateRepository(settings.data_dir / "state"),
        RssFeedPublisher(settings.data_dir / "feeds"),
        max_items=settings.max_items,
        max_concurrency=settings.max_concurrency,
    )


def build_healthchecker(client: httpx2.AsyncClient, settings: Settings) -> ScraperHealthChecker:
    return ScraperHealthChecker(
        build_scrapers(client),
        max_concurrency=settings.max_concurrency,
    )


def build_http_client() -> httpx2.AsyncClient:
    throttle = PerHostRequestThrottle(interval_seconds=1.0)
    return httpx2.AsyncClient(
        headers={
            "User-Agent": ("Mozilla/5.0 (X11; Linux x86_64; rv:156.0) Gecko/20100101 Firefox/156.0")
        },
        follow_redirects=True,
        timeout=httpx2.Timeout(20.0, connect=10.0),
        event_hooks={"request": [throttle]},
    )
