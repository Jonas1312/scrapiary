from __future__ import annotations

from scrapiary.bootstrap import build_http_client


async def test_http_client_uses_requested_firefox_user_agent() -> None:
    async with build_http_client() as client:
        assert client.headers["User-Agent"] == (
            "Mozilla/5.0 (X11; Linux x86_64; rv:156.0) Gecko/20100101 Firefox/156.0"
        )
