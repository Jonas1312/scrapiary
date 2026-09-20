from __future__ import annotations

from datetime import datetime

import httpx2
from bs4 import BeautifulSoup

from scrapiary.adapters.scrapers.common import canonicalize_url
from scrapiary.domain import FeedItem


class JacobPadillaScraper:
    slug = "jacob-padilla"
    title = "Jacob Padilla"
    home_url = "https://jacobpadilla.com/writing"

    def __init__(self, client: httpx2.AsyncClient) -> None:
        self._client = client

    async def scrape(self) -> list[FeedItem]:
        response = await self._client.get(self.home_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        items: list[FeedItem] = []
        for link in soup.select("li.writing-entry > a[href]"):
            title = link.get_text(" ", strip=True)
            href = link.get("href")
            if title and isinstance(href, str):
                url = canonicalize_url(str(response.url), href)
                items.append(await self._scrape_article(title, url))
        if not items:
            raise RuntimeError("Jacob Padilla: no articles found; the page layout may have changed")
        return items

    async def _scrape_article(self, title: str, url: str) -> FeedItem:
        response = await self._client.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        date = soup.select_one("time[datetime]")
        if date is None or not isinstance(date.get("datetime"), str):
            raise RuntimeError(f"Jacob Padilla: publication date not found for {url}")
        return FeedItem(
            title=title,
            url=url,
            published_at=datetime.fromisoformat(str(date["datetime"]).replace("Z", "+00:00")),
            author="Jacob Padilla",
        )
