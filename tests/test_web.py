from __future__ import annotations

import httpx2

from scrapiary.config import Settings
from scrapiary.web import create_app


async def test_feed_route_serves_only_known_generated_feeds(tmp_path) -> None:
    feeds = tmp_path / "feeds"
    feeds.mkdir()
    (feeds / "0byte.xml").write_text("<rss/>", encoding="utf-8")
    transport = httpx2.ASGITransport(app=create_app(Settings(data_dir=tmp_path)))

    async with httpx2.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/feeds/0byte.xml")
        unknown = await client.get("/feeds/unknown.xml")
        pending = await client.get("/feeds/abdellatif.xml")

    assert response.status_code == 200
    assert response.text == "<rss/>"
    assert response.headers["content-type"].startswith("application/rss+xml")
    assert unknown.status_code == 404
    assert pending.status_code == 404
