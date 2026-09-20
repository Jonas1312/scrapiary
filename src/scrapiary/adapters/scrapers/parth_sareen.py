from __future__ import annotations

from datetime import UTC, datetime

import httpx2
from bs4 import BeautifulSoup

from scrapiary.adapters.scrapers.common import canonicalize_url
from scrapiary.domain import FeedItem


class ParthSareenScraper:
    slug = "parth-sareen"
    title = "Parth Sareen"
    home_url = "https://parthsareen.com/writings/"

    def __init__(self, client: httpx2.AsyncClient) -> None:
        self._client = client

    async def scrape(self) -> list[FeedItem]:
        response = await self._client.get(self.home_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        items: list[FeedItem] = []
        for section in soup.select("section.year-section[data-year]"):
            year = section.get("data-year")
            if not isinstance(year, str):
                continue
            for link in section.select("a.writings-item[href]"):
                title = link.select_one(".writings-item-title")
                date = link.select_one(".writings-item-date")
                description = link.select_one(".writings-item-dek")
                href = link.get("href")
                if title is None or not isinstance(href, str):
                    continue
                if date is None:
                    raise RuntimeError("Parth Sareen: publication date not found")
                items.append(
                    FeedItem(
                        title=title.get_text(" ", strip=True),
                        url=canonicalize_url(str(response.url), href),
                        published_at=datetime.strptime(
                            f"{date.get_text(' ', strip=True)} {year}", "%b %d %Y"
                        ).replace(tzinfo=UTC),
                        description=(
                            description.get_text(" ", strip=True) if description else None
                        ),
                        author="Parth Sareen",
                    )
                )
        if not items:
            raise RuntimeError("Parth Sareen: no articles found; the page layout may have changed")
        return items
