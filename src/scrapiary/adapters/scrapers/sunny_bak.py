from __future__ import annotations

from datetime import UTC, datetime

import httpx2
from bs4 import BeautifulSoup

from scrapiary.adapters.scrapers.common import canonicalize_url
from scrapiary.domain import FeedItem


class SunnyBakScraper:
    slug = "sunny-bak"
    title = "Sunny's Blog"
    home_url = "https://www.sunnybak.net/blog"

    def __init__(self, client: httpx2.AsyncClient) -> None:
        self._client = client

    async def scrape(self) -> list[FeedItem]:
        response = await self._client.get(self.home_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        items: list[FeedItem] = []
        for link in soup.select(".post-list > a[href^='/blog/']"):
            fields = link.select("p")
            if len(fields) < 2:
                raise RuntimeError("Sunny's Blog: publication date not found")
            items.append(
                FeedItem(
                    title=fields[1].get_text(" ", strip=True),
                    url=canonicalize_url(str(response.url), str(link["href"])),
                    published_at=datetime.strptime(
                        fields[0].get_text(" ", strip=True), "%B %d, %Y"
                    ).replace(tzinfo=UTC),
                    author="Sunny Bak",
                )
            )
        if not items:
            raise RuntimeError("Sunny's Blog: no articles found; the page layout may have changed")
        return items
