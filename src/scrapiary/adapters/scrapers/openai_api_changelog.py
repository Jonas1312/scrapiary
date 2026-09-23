from __future__ import annotations

import hashlib
import re
import textwrap
from datetime import UTC, datetime

import httpx2
from bs4 import BeautifulSoup, Tag

from scrapiary.adapters.scrapers.common import canonicalize_url
from scrapiary.domain import FeedItem

MONTH_HEADING = re.compile(r"^(?P<month>[A-Za-z]+), (?P<year>\d{4})$")
FIRST_SENTENCE = re.compile(r"^(.+?[.!?])(?:\s|$)")


class OpenAIAPIChangelogScraper:
    slug = "openai-api-changelog"
    title = "OpenAI API Changelog"
    home_url = "https://developers.openai.com/api/docs/changelog"

    def __init__(self, client: httpx2.AsyncClient) -> None:
        self._client = client

    async def scrape(self) -> list[FeedItem]:
        response = await self._client.get(self.home_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        items: list[FeedItem] = []
        for heading in soup.select("h3"):
            match = MONTH_HEADING.fullmatch(heading.get_text(" ", strip=True))
            if match is None:
                continue
            for entry in heading.find_next_siblings("div", class_="mt-5"):
                items.append(
                    _parse_entry(
                        entry,
                        base_url=str(response.url),
                        month_name=match.group("month"),
                        year=int(match.group("year")),
                    )
                )

        if not items:
            raise RuntimeError(
                "OpenAI API Changelog: no entries found; the page layout may have changed"
            )
        return items


def _parse_entry(entry: Tag, *, base_url: str, month_name: str, year: int) -> FeedItem:
    date_element = entry.select_one("[data-variant='outline']")
    category_element = entry.select_one("[data-variant='soft']")
    content = entry.select_one("[class*='ChangelogMarkdown']")
    if date_element is None or category_element is None or content is None:
        raise RuntimeError("OpenAI API Changelog: entry metadata or content not found")

    published_at = _parse_date(date_element.get_text(" ", strip=True), month_name, year)
    category = category_element.get_text(" ", strip=True)
    content_text = _normalized_text(content)
    title = _make_title(category, content_text)
    fingerprint = hashlib.sha256(title.encode()).hexdigest()[:12]

    return FeedItem(
        title=title,
        url=f"{base_url}#{published_at:%Y-%m-%d}-{fingerprint}",
        published_at=published_at,
        description=_clean_content(content, base_url),
        author="OpenAI",
    )


def _parse_date(value: str, month_name: str, year: int) -> datetime:
    parsed = datetime.strptime(f"{value} {year}", "%b %d %Y")
    expected_month = datetime.strptime(month_name, "%B").month
    if parsed.month != expected_month:
        raise RuntimeError(f"OpenAI API Changelog: date {value!r} does not match {month_name}")
    return parsed.replace(tzinfo=UTC)


def _make_title(category: str, content: str) -> str:
    match = FIRST_SENTENCE.match(content)
    summary = match.group(1) if match else content
    return f"{category}: {textwrap.shorten(summary, width=140, placeholder='…')}"


def _normalized_text(content: Tag) -> str:
    text = content.get_text(" ", strip=True)
    text = re.sub(r"\s+([,.;:!?%)\]])", r"\1", text)
    return re.sub(r"([(\[])\s+", r"\1", text)


def _clean_content(content: Tag, base_url: str) -> str:
    for element in content.find_all(True):
        if element.name == "a" and isinstance(element.get("href"), str):
            element.attrs = {"href": canonicalize_url(base_url, str(element["href"]))}
        else:
            element.attrs = {}
    return "".join(str(child) for child in content.children if isinstance(child, Tag))
