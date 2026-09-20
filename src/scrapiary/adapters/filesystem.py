from __future__ import annotations

import json
import os
import tempfile
import xml.etree.ElementTree as ET
from dataclasses import asdict
from datetime import UTC, datetime
from email.utils import format_datetime
from pathlib import Path
from typing import Any

from scrapiary.domain import Feed, FeedItem, FeedState

DC_NAMESPACE = "http://purl.org/dc/elements/1.1/"
ET.register_namespace("dc", DC_NAMESPACE)


class JsonStateRepository:
    def __init__(self, directory: Path) -> None:
        self._directory = directory

    def load(self, slug: str) -> FeedState:
        path = self._path(slug)
        if not path.exists():
            return FeedState()

        raw = json.loads(path.read_text(encoding="utf-8"))
        return FeedState(
            items={item["url"]: _item_from_dict(item) for item in raw["items"]},
            last_attempt_at=_parse_datetime(raw.get("last_attempt_at")),
            last_success_at=_parse_datetime(raw.get("last_success_at")),
            last_error=raw.get("last_error"),
        )

    def save(self, slug: str, state: FeedState) -> None:
        payload = {
            "items": [_item_to_dict(item) for item in state.items.values()],
            "last_attempt_at": _format_datetime(state.last_attempt_at),
            "last_success_at": _format_datetime(state.last_success_at),
            "last_error": state.last_error,
        }
        _atomic_write(
            self._path(slug),
            (json.dumps(payload, indent=2, ensure_ascii=False) + "\n").encode(),
        )

    def _path(self, slug: str) -> Path:
        return self._directory / f"{slug}.json"


class RssFeedPublisher:
    def __init__(self, directory: Path) -> None:
        self._directory = directory

    def publish(self, feed: Feed) -> None:
        _atomic_write(self._directory / f"{feed.slug}.xml", _render_rss(feed))


def _render_rss(feed: Feed) -> bytes:
    rss = ET.Element("rss", {"version": "2.0"})
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = feed.title
    ET.SubElement(channel, "link").text = feed.home_url
    ET.SubElement(channel, "description").text = f"Articles from {feed.title}"
    ET.SubElement(channel, "lastBuildDate").text = format_datetime(feed.generated_at)

    for feed_item in feed.items:
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = feed_item.title
        ET.SubElement(item, "link").text = feed_item.url
        ET.SubElement(item, "guid", {"isPermaLink": "true"}).text = feed_item.url
        if feed_item.description:
            ET.SubElement(item, "description").text = feed_item.description
        ET.SubElement(item, "pubDate").text = format_datetime(feed_item.published_at)
        if feed_item.author:
            ET.SubElement(item, f"{{{DC_NAMESPACE}}}creator").text = feed_item.author

    ET.indent(rss)
    return ET.tostring(rss, encoding="utf-8", xml_declaration=True)


def _atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as temporary:
            temporary.write(content)
            temporary.flush()
            os.fsync(temporary.fileno())
            temporary_path = temporary.name
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None and os.path.exists(temporary_path):
            os.unlink(temporary_path)


def _item_to_dict(item: FeedItem) -> dict[str, Any]:
    raw = asdict(item)
    raw["published_at"] = _format_datetime(item.published_at)
    return raw


def _item_from_dict(raw: dict[str, Any]) -> FeedItem:
    return FeedItem(
        title=raw["title"],
        url=raw["url"],
        published_at=_parse_required_datetime(raw["published_at"]),
        description=raw.get("description"),
        author=raw.get("author"),
    )


def _format_datetime(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _parse_required_datetime(value: str) -> datetime:
    parsed = _parse_datetime(value)
    if parsed is None:
        raise ValueError("expected a datetime")
    return parsed


def _parse_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
