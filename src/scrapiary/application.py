from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from scrapiary.domain import Feed, FeedItem, FeedState, merge_items, newest_items, utc_now
from scrapiary.ports import FeedPublisher, Scraper, StateRepository

logger = logging.getLogger(__name__)


class RefreshStatus(StrEnum):
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class HealthCheckStatus(StrEnum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"


@dataclass(frozen=True, slots=True)
class RefreshResult:
    slug: str
    status: RefreshStatus
    item_count: int = 0
    error: str | None = None


@dataclass(frozen=True, slots=True)
class HealthCheckResult:
    slug: str
    status: HealthCheckStatus
    item_count: int = 0
    error: str | None = None


class ScraperHealthChecker:
    def __init__(self, scrapers: Sequence[Scraper], *, max_concurrency: int = 4) -> None:
        if max_concurrency < 1:
            raise ValueError("max_concurrency must be positive")
        self._scrapers = {scraper.slug: scraper for scraper in scrapers}
        self._semaphore = asyncio.Semaphore(max_concurrency)

    async def check_all(self) -> tuple[HealthCheckResult, ...]:
        return tuple(await asyncio.gather(*(self.check(slug) for slug in self._scrapers)))

    async def check(self, slug: str) -> HealthCheckResult:
        scraper = self._scrapers.get(slug)
        if scraper is None:
            raise KeyError(f"unknown scraper: {slug}")

        async with self._semaphore:
            try:
                items = await _scrape_nonempty(scraper)
            except Exception as exc:
                return HealthCheckResult(
                    slug=slug,
                    status=HealthCheckStatus.UNHEALTHY,
                    error=str(exc),
                )

        return HealthCheckResult(
            slug=slug,
            status=HealthCheckStatus.HEALTHY,
            item_count=len(items),
        )


class FeedRefresher:
    def __init__(
        self,
        scrapers: Sequence[Scraper],
        states: StateRepository,
        publisher: FeedPublisher,
        *,
        max_items: int = 100,
        max_concurrency: int = 4,
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        if max_items < 1:
            raise ValueError("max_items must be positive")
        if max_concurrency < 1:
            raise ValueError("max_concurrency must be positive")

        self._scrapers = {scraper.slug: scraper for scraper in scrapers}
        self._states = states
        self._publisher = publisher
        self._max_items = max_items
        self._semaphore = asyncio.Semaphore(max_concurrency)
        self._locks = {slug: asyncio.Lock() for slug in self._scrapers}
        self._clock = clock

    @property
    def slugs(self) -> tuple[str, ...]:
        return tuple(self._scrapers)

    async def refresh_all(self) -> tuple[RefreshResult, ...]:
        return tuple(await asyncio.gather(*(self.refresh(slug) for slug in self.slugs)))

    async def refresh(self, slug: str) -> RefreshResult:
        scraper = self._scrapers.get(slug)
        if scraper is None:
            raise KeyError(f"unknown scraper: {slug}")

        lock = self._locks[slug]
        if lock.locked():
            return RefreshResult(slug=slug, status=RefreshStatus.SKIPPED)

        async with lock, self._semaphore:
            attempted_at = self._clock()
            try:
                state = self._states.load(slug)
                items = await _scrape_nonempty(scraper)
                state = merge_items(state, items, attempted_at)
                feed = Feed(
                    slug=slug,
                    title=scraper.title,
                    home_url=scraper.home_url,
                    items=newest_items(state, self._max_items),
                    generated_at=attempted_at,
                )
                self._publisher.publish(feed)
                self._states.save(slug, state)
            except Exception as exc:
                logger.exception("Failed to refresh %s", slug)
                self._record_failure(slug, attempted_at, str(exc))
                return RefreshResult(
                    slug=slug,
                    status=RefreshStatus.FAILED,
                    error=str(exc),
                )

            logger.info("Refreshed %s with %d scraped items", slug, len(items))
            return RefreshResult(
                slug=slug,
                status=RefreshStatus.SUCCESS,
                item_count=len(items),
            )

    def _record_failure(self, slug: str, attempted_at: datetime, error: str) -> None:
        try:
            state = self._states.load(slug)
            failed_state = FeedState(
                items=state.items,
                last_attempt_at=attempted_at,
                last_success_at=state.last_success_at,
                last_error=error,
            )
            self._states.save(slug, failed_state)
        except Exception:
            logger.exception("Could not persist failure status for %s", slug)


async def _scrape_nonempty(scraper: Scraper) -> list[FeedItem]:
    items = await scraper.scrape()
    if not items:
        raise RuntimeError("scraper returned no articles")
    return items
