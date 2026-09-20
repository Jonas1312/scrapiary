from __future__ import annotations

from datetime import UTC, datetime

import httpx2
from bs4 import BeautifulSoup

from scrapiary.adapters.scrapers.common import canonicalize_url
from scrapiary.domain import FeedItem


class ClaudeCookbookScraper:
    slug = "claude-cookbook"
    title = "Claude Cookbook"
    home_url = "https://platform.claude.com/cookbook/"

    def __init__(self, client: httpx2.AsyncClient) -> None:
        self._client = client

    async def scrape(self) -> list[FeedItem]:
        response = await self._client.get(self.home_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        items: list[FeedItem] = []
        for row in soup.select("tbody tr"):
            link = row.select_one("a[href^='/cookbook/']:not([href*='?'])")
            title = row.select_one("span.font-medium.text-primary")
            description = row.select_one("p.text-body")
            if link is None or title is None:
                continue
            url = canonicalize_url(str(response.url), str(link["href"]))
            items.append(
                await self._scrape_recipe(
                    title.get_text(" ", strip=True),
                    url,
                    description.get_text(" ", strip=True) if description else None,
                )
            )
        if not items:
            raise RuntimeError(
                "Claude Cookbook: no articles found; the page layout may have changed"
            )
        return items

    async def _scrape_recipe(self, title: str, url: str, description: str | None) -> FeedItem:
        response = await self._client.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        published = next(
            (
                value
                for element in soup.select("header .text-body.text-muted")
                if (value := element.get_text(" ", strip=True)).startswith("Published on")
            ),
            None,
        )
        if published is None:
            raise RuntimeError(f"Claude Cookbook: publication date not found for {url}")
        value = published.removeprefix("Published on ")
        author_image = soup.select_one("header img[alt]")
        return FeedItem(
            title=title,
            url=url,
            published_at=datetime.strptime(value, "%B %d, %Y").replace(tzinfo=UTC),
            description=description,
            author=str(author_image["alt"]) if author_image else None,
        )
