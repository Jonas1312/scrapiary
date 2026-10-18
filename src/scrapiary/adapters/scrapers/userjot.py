from __future__ import annotations

from datetime import UTC, datetime

import httpx2
from bs4 import BeautifulSoup

from scrapiary.adapters.scrapers.common import canonicalize_url
from scrapiary.domain import FeedItem


class UserJotEngineeringScraper:
    slug = "userjot-engineering"
    title = "UserJot Engineering"
    home_url = "https://userjot.com/blog?category=engineering"

    def __init__(self, client: httpx2.AsyncClient) -> None:
        self._client = client

    async def scrape(self) -> list[FeedItem]:
        response = await self._client.get(self.home_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        items: list[FeedItem] = []
        for link in soup.select("a[href^='/blog/']"):
            title = link.select_one("h2, h3")
            date = link.select_one("time[datetime]")
            categories = {
                category.get_text(" ", strip=True) for category in link.select("span")
            }
            if "Engineering" not in categories:
                continue
            if title is None:
                continue
            if date is None or not isinstance(date.get("datetime"), str):
                raise RuntimeError("UserJot Engineering: publication date not found")
            summary = next(
                (
                    paragraph
                    for paragraph in link.select("p")
                    if paragraph.select_one("time") is None
                ),
                None,
            )
            items.append(
                FeedItem(
                    title=title.get_text(" ", strip=True),
                    url=canonicalize_url(str(response.url), str(link["href"])),
                    published_at=datetime.strptime(str(date["datetime"]), "%Y-%m-%d").replace(
                        tzinfo=UTC
                    ),
                    description=summary.get_text(" ", strip=True) if summary else None,
                    author="UserJot",
                )
            )
        if not items:
            raise RuntimeError(
                "UserJot Engineering: no articles found; the page layout may have changed"
            )
        return items
