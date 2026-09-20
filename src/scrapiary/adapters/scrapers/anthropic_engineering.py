from __future__ import annotations

from datetime import UTC, datetime

import httpx2
from bs4 import BeautifulSoup, Tag

from scrapiary.adapters.scrapers.common import canonicalize_url
from scrapiary.domain import FeedItem


class AnthropicEngineeringScraper:
    slug = "anthropic-engineering"
    title = "Anthropic Engineering"
    home_url = "https://www.anthropic.com/engineering"

    def __init__(self, client: httpx2.AsyncClient) -> None:
        self._client = client

    async def scrape(self) -> list[FeedItem]:
        response = await self._client.get(self.home_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        items: list[FeedItem] = []
        for article in soup.select("article[class*='ArticleList']"):
            link = article.select_one("a[href^='/engineering/']")
            title = article.select_one("h2, h3")
            if link is None or title is None:
                continue
            url = canonicalize_url(str(response.url), str(link["href"]))
            date = article.select_one("[class*='date']")
            description = article.select_one("[class*='summary']")
            published_at = (
                _parse_date(date.get_text(" ", strip=True))
                if date is not None
                else await self._scrape_article_date(url)
            )
            items.append(
                FeedItem(
                    title=title.get_text(" ", strip=True),
                    url=url,
                    published_at=published_at,
                    description=(
                        description.get_text(" ", strip=True)
                        if isinstance(description, Tag)
                        else None
                    ),
                    author="Anthropic",
                )
            )
        if not items:
            raise RuntimeError(
                "Anthropic Engineering: no articles found; the page layout may have changed"
            )
        return items

    async def _scrape_article_date(self, url: str) -> datetime:
        response = await self._client.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        date = soup.select_one("[class*='HeroEngineering'][class*='date']")
        if date is None:
            raise RuntimeError(f"Anthropic Engineering: publication date not found for {url}")
        return _parse_date(date.get_text(" ", strip=True).removeprefix("Published "))


def _parse_date(value: str) -> datetime:
    return datetime.strptime(value, "%b %d, %Y").replace(tzinfo=UTC)
