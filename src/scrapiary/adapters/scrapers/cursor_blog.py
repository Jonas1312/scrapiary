from __future__ import annotations

from datetime import datetime

import httpx2
from bs4 import BeautifulSoup

from scrapiary.adapters.scrapers.common import canonicalize_url
from scrapiary.domain import FeedItem


class CursorBlogScraper:
    slug = "cursor-blog"
    title = "Cursor Blog"
    home_url = "https://cursor.com/blog"

    def __init__(self, client: httpx2.AsyncClient) -> None:
        self._client = client

    async def scrape(self) -> list[FeedItem]:
        response = await self._client.get(self.home_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        items: list[FeedItem] = []
        seen_urls: set[str] = set()
        for link in soup.select(".blog-directory__item > a[href]"):
            title = link.select_one("article p")
            date = link.select_one("time[datetime]")
            href = link.get("href")
            if title is None or not isinstance(href, str):
                continue
            if date is None or not isinstance(date.get("datetime"), str):
                raise RuntimeError("Cursor Blog: publication date not found")
            url = canonicalize_url(str(response.url), href)
            if url in seen_urls:
                continue
            seen_urls.add(url)
            items.append(
                FeedItem(
                    title=" ".join(title.get_text(" ", strip=True).split()),
                    url=url,
                    published_at=datetime.fromisoformat(str(date["datetime"])),
                    author="Cursor",
                )
            )
        if not items:
            raise RuntimeError("Cursor Blog: no articles found; the page layout may have changed")
        return items
