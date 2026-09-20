from __future__ import annotations

import re
from datetime import UTC, datetime

import httpx2
from bs4 import BeautifulSoup

from scrapiary.adapters.scrapers.common import canonicalize_url
from scrapiary.domain import FeedItem


class ZeroByteScraper:
    slug = "0byte"
    title = "0byte"
    home_url = "https://0byte.io/"

    def __init__(self, client: httpx2.AsyncClient) -> None:
        self._client = client

    async def scrape(self) -> list[FeedItem]:
        response = await self._client.get(self.home_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        items: list[FeedItem] = []
        for link in soup.select(".articleelement > a[href]"):
            title = link.get_text(" ", strip=True)
            href = link.get("href")
            if title and isinstance(href, str):
                url = canonicalize_url(str(response.url), href)
                items.append(await self._scrape_article(title, url))
        if not items:
            raise RuntimeError("0byte: no articles found; the page layout may have changed")
        return items

    async def _scrape_article(self, title: str, url: str) -> FeedItem:
        response = await self._client.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        date = soup.select_one(".date-created")
        introduction = soup.select_one("p.section")
        return FeedItem(
            title=title,
            url=url,
            description=(
                " ".join(introduction.get_text(" ", strip=True).split()) if introduction else None
            ),
            published_at=_parse_date(date.get_text(" ", strip=True) if date else None),
        )


def _parse_date(value: str | None) -> datetime:
    if value is None:
        raise RuntimeError("0byte: publication date not found")
    without_ordinal = re.sub(r"(\d+)(?:st|nd|rd|th)", r"\1", value, flags=re.IGNORECASE)
    return datetime.strptime(without_ordinal, "%d %B, %Y").replace(tzinfo=UTC)
