from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime

from scrapiary.application import (
    FeedRefresher,
    HealthCheckStatus,
    RefreshStatus,
    ScraperHealthChecker,
)
from scrapiary.domain import Feed, FeedItem, FeedState


@dataclass
class MemoryStates:
    value: FeedState

    def load(self, slug: str) -> FeedState:
        del slug
        return self.value

    def save(self, slug: str, state: FeedState) -> None:
        del slug
        self.value = state


@dataclass
class MemoryPublisher:
    feed: Feed | None = None

    def publish(self, feed: Feed) -> None:
        self.feed = feed


class StubScraper:
    slug = "example"
    title = "Example"
    home_url = "https://example.com"

    def __init__(self, items: list[FeedItem] | None = None, error: Exception | None = None) -> None:
        self._items = items or []
        self._error = error

    async def scrape(self) -> list[FeedItem]:
        if self._error:
            raise self._error
        return self._items


class BlockingScraper(StubScraper):
    def __init__(self) -> None:
        super().__init__()
        self.started = asyncio.Event()
        self.release = asyncio.Event()

    async def scrape(self) -> list[FeedItem]:
        self.started.set()
        await self.release.wait()
        return [FeedItem("Current", "https://example.com/current", datetime.now(UTC))]


async def test_refresh_publishes_current_and_previous_items() -> None:
    now = datetime(2026, 9, 20, 8, 0, tzinfo=UTC)
    previous = FeedItem("Previous", "https://example.com/previous", now)
    states = MemoryStates(FeedState())
    states.value.items[previous.url] = previous
    publisher = MemoryPublisher()
    refresher = FeedRefresher(
        [StubScraper([FeedItem("Current", "https://example.com/current", now)])],
        states,
        publisher,
        clock=lambda: now,
    )

    result = await refresher.refresh("example")

    assert result.status is RefreshStatus.SUCCESS
    assert publisher.feed is not None
    assert {item.title for item in publisher.feed.items} == {"Previous", "Current"}


async def test_failed_refresh_preserves_feed_and_items_but_records_error() -> None:
    now = datetime(2026, 9, 20, 8, 0, tzinfo=UTC)
    state = FeedState(last_success_at=now)
    states = MemoryStates(state)
    existing_feed = Feed("example", "Example", "https://example.com", (), now)
    publisher = MemoryPublisher(existing_feed)
    refresher = FeedRefresher(
        [StubScraper(error=RuntimeError("website unavailable"))],
        states,
        publisher,
        clock=lambda: now,
    )

    result = await refresher.refresh("example")

    assert result.status is RefreshStatus.FAILED
    assert publisher.feed is existing_feed
    assert states.value.last_success_at == now
    assert states.value.last_error == "website unavailable"


async def test_empty_refresh_is_a_failure_and_preserves_the_feed() -> None:
    now = datetime(2026, 9, 20, 8, 0, tzinfo=UTC)
    states = MemoryStates(FeedState(last_success_at=now))
    existing_feed = Feed("example", "Example", "https://example.com", (), now)
    publisher = MemoryPublisher(existing_feed)
    refresher = FeedRefresher(
        [StubScraper()],
        states,
        publisher,
        clock=lambda: now,
    )

    result = await refresher.refresh("example")

    assert result.status is RefreshStatus.FAILED
    assert result.error == "scraper returned no articles"
    assert publisher.feed is existing_feed
    assert states.value.last_error == "scraper returned no articles"


async def test_overlapping_refresh_of_same_site_is_skipped() -> None:
    now = datetime(2026, 9, 20, 8, 0, tzinfo=UTC)
    scraper = BlockingScraper()
    refresher = FeedRefresher(
        [scraper],
        MemoryStates(FeedState()),
        MemoryPublisher(),
        clock=lambda: now,
    )
    first = asyncio.create_task(refresher.refresh("example"))
    await scraper.started.wait()

    overlapping = await refresher.refresh("example")
    scraper.release.set()
    completed = await first

    assert overlapping.status is RefreshStatus.SKIPPED
    assert completed.status is RefreshStatus.SUCCESS


async def test_healthcheck_reports_success_failure_and_empty_results() -> None:
    healthy = StubScraper([FeedItem("Current", "https://example.com/current", datetime.now(UTC))])
    healthy.slug = "healthy"
    broken = StubScraper(error=RuntimeError("website unavailable"))
    broken.slug = "broken"
    empty = StubScraper()
    empty.slug = "empty"
    healthchecker = ScraperHealthChecker([healthy, broken, empty], max_concurrency=2)

    results = await healthchecker.check_all()

    assert [
        (result.slug, result.status, result.item_count, result.error) for result in results
    ] == [
        ("healthy", HealthCheckStatus.HEALTHY, 1, None),
        ("broken", HealthCheckStatus.UNHEALTHY, 0, "website unavailable"),
        ("empty", HealthCheckStatus.UNHEALTHY, 0, "scraper returned no articles"),
    ]
