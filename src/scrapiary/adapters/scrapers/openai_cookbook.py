from __future__ import annotations

from datetime import UTC, datetime

import httpx2
from bs4 import BeautifulSoup

from scrapiary.adapters.scrapers.common import canonicalize_url
from scrapiary.domain import FeedItem


class OpenAICookbookScraper:
    slug = "openai-cookbook"
    title = "OpenAI Cookbook"
    home_url = "https://developers.openai.com/cookbook"

    def __init__(self, client: httpx2.AsyncClient) -> None:
        self._client = client

    async def scrape(self) -> list[FeedItem]:
        response = await self._client.get(self.home_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        items: list[FeedItem] = []
        for link in soup.select("a.recipe-row[href]"):
            title = link.select_one(".recipe-title")
            date = link.select_one("time[datetime]")
            if title is None or not isinstance(link.get("href"), str):
                continue
            if date is None:
                raise RuntimeError("OpenAI Cookbook: publication date not found")
            items.append(
                FeedItem(
                    title=title.get_text(" ", strip=True),
                    url=canonicalize_url(str(response.url), str(link["href"])),
                    published_at=_parse_date(str(date["datetime"])),
                )
            )
        if not items:
            raise RuntimeError(
                "OpenAI Cookbook: no articles found; the page layout may have changed"
            )
        return items


def _parse_date(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=UTC)
