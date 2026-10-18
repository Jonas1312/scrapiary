from __future__ import annotations

from datetime import UTC, datetime

import httpx2
from bs4 import BeautifulSoup
from bs4.element import Tag

from scrapiary.adapters.scrapers.common import canonicalize_url
from scrapiary.domain import FeedItem


class ClaudeBlogScraper:
    slug = "claude-blog"
    title = "Claude Blog"
    home_url = "https://claude.com/resources/articles"

    def __init__(self, client: httpx2.AsyncClient) -> None:
        self._client = client

    async def scrape(self) -> list[FeedItem]:
        response = await self._client.get(self.home_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        items: list[FeedItem] = []
        seen_urls: set[str] = set()
        for link in soup.select("a[href]:has(h3)"):
            title = link.select_one("h3")
            href = link.get("href")
            if title is None or not isinstance(href, str):
                continue
            published_at = _find_date(link.select("span"))
            if published_at is None:
                raise RuntimeError("Claude Blog: publication date not found")
            url = canonicalize_url(str(response.url), href)
            if url in seen_urls:
                continue
            seen_urls.add(url)
            summary = link.select_one("p")
            items.append(
                FeedItem(
                    title=title.get_text(" ", strip=True),
                    url=url,
                    published_at=published_at,
                    description=summary.get_text(" ", strip=True) if summary else None,
                    author="Anthropic",
                )
            )
        if not items:
            raise RuntimeError("Claude Blog: no articles found; the page layout may have changed")
        return items


def _find_date(metadata: list[Tag]) -> datetime | None:
    for element in metadata:
        value = element.get_text(" ", strip=True)
        for date_format in ("%b %d, %Y", "%B %d, %Y"):
            try:
                return datetime.strptime(value, date_format).replace(tzinfo=UTC)
            except ValueError:
                continue
    return None
