from __future__ import annotations

from typing import Protocol

from scrapiary.domain import Feed, FeedItem, FeedState


class Scraper(Protocol):
    slug: str
    title: str
    home_url: str

    async def scrape(self) -> list[FeedItem]: ...


class StateRepository(Protocol):
    def load(self, slug: str) -> FeedState: ...

    def save(self, slug: str, state: FeedState) -> None: ...


class FeedPublisher(Protocol):
    def publish(self, feed: Feed) -> None: ...
