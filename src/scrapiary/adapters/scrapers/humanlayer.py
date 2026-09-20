from __future__ import annotations

from datetime import UTC, datetime

import httpx2
from bs4 import BeautifulSoup

from scrapiary.adapters.scrapers.common import canonicalize_url
from scrapiary.domain import FeedItem


class HumanLayerScraper:
    slug = "humanlayer"
    title = "HumanLayer Blog"
    home_url = "https://www.humanlayer.dev/blog"

    def __init__(self, client: httpx2.AsyncClient) -> None:
        self._client = client

    async def scrape(self) -> list[FeedItem]:
        response = await self._client.get(self.home_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        items: list[FeedItem] = []
        for link in soup.select("a.block.py-2.group[href^='/blog/']"):
            title = link.select_one("h2")
            metadata = link.select_one("p.text-sm")
            if title is None:
                continue
            if metadata is None:
                raise RuntimeError("HumanLayer Blog: publication date not found")
            parts = [part.strip() for part in metadata.get_text(" ", strip=True).split("·")]
            if len(parts) < 2:
                raise RuntimeError("HumanLayer Blog: publication date not found")
            paragraphs = link.select("p")
            items.append(
                FeedItem(
                    title=title.get_text(" ", strip=True),
                    url=canonicalize_url(str(response.url), str(link["href"])),
                    published_at=datetime.strptime(parts[1], "%B %d, %Y").replace(tzinfo=UTC),
                    description=(
                        paragraphs[-1].get_text(" ", strip=True) if len(paragraphs) > 1 else None
                    ),
                    author=parts[0],
                )
            )
        if not items:
            raise RuntimeError(
                "HumanLayer Blog: no articles found; the page layout may have changed"
            )
        return items
