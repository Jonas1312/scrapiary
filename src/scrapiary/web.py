from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from scrapiary.application import FeedRefresher
from scrapiary.bootstrap import build_http_client, build_refresher
from scrapiary.config import Settings
from scrapiary.registry import SCRAPERS

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        async with build_http_client() as client:
            refresher = build_refresher(client, settings)
            scheduler = asyncio.create_task(
                _run_scheduler(refresher, settings.refresh_hours * 60 * 60),
                name="scrapiary-scheduler",
            )
            yield
            scheduler.cancel()
            with suppress(asyncio.CancelledError):
                await scheduler

    app = FastAPI(title="Scrapiary", lifespan=lifespan)
    known_slugs = {definition.slug for definition in SCRAPERS}

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/feeds/{slug}.xml", response_class=FileResponse)
    async def feed(slug: str) -> FileResponse:
        if slug not in known_slugs:
            raise HTTPException(status_code=404, detail="Unknown feed")
        path = settings.data_dir / "feeds" / f"{slug}.xml"
        if not path.is_file():
            raise HTTPException(status_code=404, detail="Feed has not been generated yet")
        return FileResponse(path, media_type="application/rss+xml")

    return app


async def _run_scheduler(refresher: FeedRefresher, interval_seconds: float) -> None:
    while True:
        try:
            await refresher.refresh_all()
        except Exception:
            logger.exception("Unexpected scheduler failure")
        await asyncio.sleep(interval_seconds)
