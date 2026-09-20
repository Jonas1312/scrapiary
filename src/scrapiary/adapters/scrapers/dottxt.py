from __future__ import annotations

from datetime import UTC, datetime

import httpx2
from bs4 import BeautifulSoup

from scrapiary.adapters.scrapers.common import canonicalize_url
from scrapiary.domain import FeedItem


class DotTxtScraper:
    slug = "dottxt"
    title = ".txt Engineering"
    home_url = "https://blog.dottxt.ai/index.html"

    def __init__(self, client: httpx2.AsyncClient) -> None:
        self._client = client

    async def scrape(self) -> list[FeedItem]:
        response = await self._client.get(self.home_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        items: list[FeedItem] = []
        for row in soup.select("ul.org-ul > li"):
            link = row.select_one("a[href]")
            if link is None or not isinstance(link.get("href"), str):
                continue
            items.append(
                FeedItem(
                    title=link.get_text(" ", strip=True),
                    url=canonicalize_url(str(response.url), str(link["href"])),
                    published_at=_parse_date(row.get_text(" ", strip=True)[:10]),
                    author=".txt team",
                )
            )
        if not items:
            raise RuntimeError(".txt: no articles found; the page layout may have changed")
        return items


def _parse_date(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=UTC)
