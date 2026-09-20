from __future__ import annotations

from datetime import UTC, datetime

import httpx2
from bs4 import BeautifulSoup

from scrapiary.adapters.scrapers.common import canonicalize_url
from scrapiary.domain import FeedItem


class UserJotEngineeringScraper:
    slug = "userjot-engineering"
    title = "UserJot Engineering"
    home_url = "https://userjot.com/blog?category=engineering"

    def __init__(self, client: httpx2.AsyncClient) -> None:
        self._client = client

    async def scrape(self) -> list[FeedItem]:
        response = await self._client.get(self.home_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        items: list[FeedItem] = []
        for link in soup.select("li > a[href^='/blog/']"):
            title = link.select_one("h2")
            date = link.select_one("time[datetime]")
            metadata = link.select_one("div")
            category = metadata.select_one("span") if metadata else None
            if category is None or category.get_text(" ", strip=True) != "Engineering":
                continue
            if title is None:
                continue
            if date is None or not isinstance(date.get("datetime"), str):
                raise RuntimeError("UserJot Engineering: publication date not found")
            summary = link.select_one("p")
            items.append(
                FeedItem(
                    title=title.get_text(" ", strip=True),
                    url=canonicalize_url(str(response.url), str(link["href"])),
                    published_at=datetime.strptime(str(date["datetime"]), "%Y-%m-%d").replace(
                        tzinfo=UTC
                    ),
                    description=summary.get_text(" ", strip=True) if summary else None,
                    author="UserJot",
                )
            )
        if not items:
            raise RuntimeError(
                "UserJot Engineering: no articles found; the page layout may have changed"
            )
        return items
