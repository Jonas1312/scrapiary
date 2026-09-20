from __future__ import annotations

from datetime import UTC, datetime

from scrapiary.domain import FeedItem, FeedState, merge_items, newest_items


def test_merge_retains_missing_items_and_updates_existing_items() -> None:
    first_seen = datetime(2026, 1, 1, tzinfo=UTC)
    published = datetime(2025, 12, 1, tzinfo=UTC)
    initial = merge_items(
        FeedState(),
        [
            FeedItem(title="First", url="https://example.com/first", published_at=published),
            FeedItem(
                title="Missing later",
                url="https://example.com/missing",
                published_at=datetime(2025, 11, 1, tzinfo=UTC),
            ),
        ],
        first_seen,
    )

    refreshed = merge_items(
        initial,
        [
            FeedItem(
                title="First, corrected",
                url="https://example.com/first",
                published_at=published,
            )
        ],
        datetime(2026, 1, 2, tzinfo=UTC),
    )

    assert set(refreshed.items) == {
        "https://example.com/first",
        "https://example.com/missing",
    }
    first = refreshed.items["https://example.com/first"]
    assert first.title == "First, corrected"
    assert first.published_at == published


def test_newest_items_uses_publication_date() -> None:
    state = merge_items(
        FeedState(),
        [
            FeedItem(
                title="New",
                url="https://example.com/new",
                published_at=datetime(2026, 1, 2, tzinfo=UTC),
            )
        ],
        datetime(2026, 1, 1, tzinfo=UTC),
    )
    state = merge_items(
        state,
        [
            FeedItem(
                title="Old",
                url="https://example.com/old",
                published_at=datetime(2026, 1, 1, tzinfo=UTC),
            )
        ],
        datetime(2026, 1, 2, tzinfo=UTC),
    )

    assert [item.title for item in newest_items(state, 1)] == ["New"]
