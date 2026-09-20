from __future__ import annotations

from datetime import UTC, datetime

import httpx2
from bs4 import BeautifulSoup

from scrapiary.adapters.scrapers.common import canonicalize_url
from scrapiary.domain import FeedItem


class AbdellatifScraper:
    slug = "abdellatif"
    title = "Abdellatif Abdelfattah"
    home_url = "https://blog.abdellatif.io/"

    def __init__(self, client: httpx2.AsyncClient) -> None:
        self._client = client

    async def scrape(self) -> list[FeedItem]:
        response = await self._client.get(self.home_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        items: list[FeedItem] = []
        for link in soup.select("main section .my-8 a[href]"):
            parts = link.select("p")
            if not isinstance(link.get("href"), str):
                continue
            if len(parts) != 2:
                raise RuntimeError("Abdellatif: publication date not found")
            items.append(
                FeedItem(
                    title=parts[1].get_text(" ", strip=True),
                    url=canonicalize_url(str(response.url), str(link["href"])),
                    published_at=_parse_date(parts[0].get_text(" ", strip=True)),
                    author="Abdellatif Abdelfattah",
                )
            )
        if not items:
            raise RuntimeError("Abdellatif: no articles found; the page layout may have changed")
        return items


def _parse_date(value: str | None) -> datetime:
    if value is None:
        raise RuntimeError("Abdellatif: publication date not found")
    return datetime.strptime(value, "%B %d, %Y").replace(tzinfo=UTC)
