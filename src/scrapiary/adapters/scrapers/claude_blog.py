from __future__ import annotations

from datetime import UTC, datetime

import httpx2
from bs4 import BeautifulSoup

from scrapiary.adapters.scrapers.common import canonicalize_url
from scrapiary.domain import FeedItem


class ClaudeBlogScraper:
    slug = "claude-blog"
    title = "Claude Blog"
    home_url = "https://claude.com/blog"

    def __init__(self, client: httpx2.AsyncClient) -> None:
        self._client = client

    async def scrape(self) -> list[FeedItem]:
        response = await self._client.get(self.home_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        items: list[FeedItem] = []
        for card in soup.select(".blog_cms_grid > .blog_cms_item"):
            link = card.select_one("a[data-cta-position='Blog grid'][href^='/blog/']")
            title = card.select_one(".card_blog_title")
            date = card.select_one("[fs-list-field='date']")
            if link is None or title is None:
                continue
            if date is None:
                raise RuntimeError("Claude Blog: publication date not found")
            items.append(
                FeedItem(
                    title=title.get_text(" ", strip=True),
                    url=canonicalize_url(str(response.url), str(link["href"])),
                    published_at=_parse_date(date.get_text(" ", strip=True)),
                    author="Anthropic",
                )
            )
        if not items:
            raise RuntimeError("Claude Blog: no articles found; the page layout may have changed")
        return items


def _parse_date(value: str) -> datetime:
    return datetime.strptime(value, "%B %d, %Y").replace(tzinfo=UTC)
