from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import UTC, datetime

from scrapiary.adapters.filesystem import JsonStateRepository, RssFeedPublisher
from scrapiary.domain import Feed, FeedItem, FeedState


def test_json_state_round_trip(tmp_path) -> None:
    repository = JsonStateRepository(tmp_path)
    when = datetime(2026, 9, 20, 8, 0, tzinfo=UTC)
    state = FeedState(
        items={
            "https://example.com/post": FeedItem(
                "Post", "https://example.com/post", when, author="Someone"
            )
        },
        last_attempt_at=when,
        last_success_at=when,
    )

    repository.save("example", state)

    assert repository.load("example") == state
    assert not list(tmp_path.glob("tmp*"))


def test_rss_uses_url_as_guid_and_includes_publication_date(tmp_path) -> None:
    when = datetime(2026, 9, 20, 8, 0, tzinfo=UTC)
    item = FeedItem(
        title="A <safe> title",
        url="https://example.com/post?id=1&view=full",
        published_at=when,
        description='<p>A <a href="https://example.com/details">rich summary</a></p>',
        author="An Author",
    )
    feed = Feed("example", "Example", "https://example.com", (item,), when)

    RssFeedPublisher(tmp_path).publish(feed)

    root = ET.parse(tmp_path / "example.xml").getroot()
    rss_item = root.find("./channel/item")
    assert rss_item is not None
    assert rss_item.findtext("guid") == item.url
    assert rss_item.find("guid").attrib == {"isPermaLink": "true"}  # type: ignore[union-attr]
    assert rss_item.findtext("pubDate") == "Sun, 20 Sep 2026 08:00:00 +0000"
    assert rss_item.findtext("title") == "A <safe> title"
    assert rss_item.findtext("description") == (
        '<p>A <a href="https://example.com/details">rich summary</a></p>'
    )
