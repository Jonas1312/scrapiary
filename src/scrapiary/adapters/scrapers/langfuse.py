from __future__ import annotations

import re
from datetime import UTC, datetime

import httpx2
from bs4 import BeautifulSoup

from scrapiary.adapters.scrapers.common import canonicalize_url
from scrapiary.domain import FeedItem

DATE_IN_PATH = re.compile(r"^/changelog/(\d{4}-\d{2}-\d{2})-")


class LangfuseChangelogScraper:
    slug = "langfuse-changelog"
    title = "Langfuse Changelog"
    home_url = "https://langfuse.com/changelog"

    def __init__(self, client: httpx2.AsyncClient) -> None:
        self._client = client

    async def scrape(self) -> list[FeedItem]:
        response = await self._client.get(self.home_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        items: list[FeedItem] = []
        for link in soup.select("a[href^='/changelog/']"):
            href = link.get("href")
            title = link.select_one("h2, h3, h4")
            if not isinstance(href, str) or title is None:
                continue
            match = DATE_IN_PATH.match(href)
            if match is None:
                raise RuntimeError(f"Langfuse Changelog: publication date not found for {href}")
            items.append(
                FeedItem(
                    title=title.get_text(" ", strip=True),
                    url=canonicalize_url(str(response.url), href),
                    published_at=datetime.strptime(match.group(1), "%Y-%m-%d").replace(tzinfo=UTC),
                    author="Langfuse",
                )
            )
        if not items:
            raise RuntimeError(
                "Langfuse Changelog: no articles found; the page layout may have changed"
            )
        return items
