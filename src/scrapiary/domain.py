from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


def utc_now() -> datetime:
    return datetime.now(UTC)


def require_aware(value: datetime | None) -> None:
    if value is not None and value.tzinfo is None:
        raise ValueError("datetimes must include a timezone")


@dataclass(frozen=True, slots=True)
class FeedItem:
    title: str
    url: str
    published_at: datetime
    description: str | None = None
    author: str | None = None

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("item title must not be empty")
        if not self.url.startswith(("http://", "https://")):
            raise ValueError("item URL must be absolute")
        require_aware(self.published_at)


@dataclass(slots=True)
class FeedState:
    items: dict[str, FeedItem] = field(default_factory=dict)
    last_attempt_at: datetime | None = None
    last_success_at: datetime | None = None
    last_error: str | None = None

    def __post_init__(self) -> None:
        require_aware(self.last_attempt_at)
        require_aware(self.last_success_at)


@dataclass(frozen=True, slots=True)
class Feed:
    slug: str
    title: str
    home_url: str
    items: tuple[FeedItem, ...]
    generated_at: datetime

    def __post_init__(self) -> None:
        require_aware(self.generated_at)


def merge_items(
    state: FeedState,
    scraped_items: list[FeedItem],
    seen_at: datetime,
) -> FeedState:
    require_aware(seen_at)
    merged = dict(state.items)

    for item in scraped_items:
        merged[item.url] = item

    return FeedState(
        items=merged,
        last_attempt_at=seen_at,
        last_success_at=seen_at,
        last_error=None,
    )


def newest_items(state: FeedState, limit: int) -> tuple[FeedItem, ...]:
    ordered = sorted(
        state.items.values(),
        key=lambda item: item.published_at,
        reverse=True,
    )
    return tuple(ordered[:limit])
