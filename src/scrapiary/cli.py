from __future__ import annotations

import argparse
import asyncio
import logging
from pathlib import Path
from typing import NoReturn

import uvicorn

from scrapiary.application import HealthCheckStatus, RefreshStatus
from scrapiary.bootstrap import build_healthchecker, build_http_client, build_refresher
from scrapiary.config import Settings
from scrapiary.registry import SCRAPERS
from scrapiary.web import create_app


def main() -> None:
    args = _parser().parse_args()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    settings = _settings_from_args(args)
    if args.command == "serve":
        uvicorn.run(create_app(settings), host=settings.host, port=settings.port)
    elif args.command == "refresh":
        raise SystemExit(asyncio.run(_refresh(settings, args.site)))
    elif args.command == "healthcheck":
        raise SystemExit(asyncio.run(_healthcheck(settings, args.site)))
    elif args.command == "list":
        for definition in SCRAPERS:
            feed_url = f"http://{settings.host}:{settings.port}/feeds/{definition.slug}.xml"
            print(feed_url)
    else:
        _unreachable(args.command)


async def _refresh(settings: Settings, site: str | None) -> int:
    async with build_http_client() as client:
        refresher = build_refresher(client, settings)
        if site is not None:
            try:
                results = (await refresher.refresh(site),)
            except KeyError as exc:
                print(exc.args[0])
                return 2
        else:
            results = await refresher.refresh_all()

    for result in results:
        detail = f": {result.error}" if result.error else ""
        print(f"{result.slug}: {result.status}{detail}")
    return int(any(result.status is RefreshStatus.FAILED for result in results))


async def _healthcheck(settings: Settings, site: str | None) -> int:
    async with build_http_client() as client:
        healthchecker = build_healthchecker(client, settings)
        if site is not None:
            try:
                results = (await healthchecker.check(site),)
            except KeyError as exc:
                print(exc.args[0])
                return 2
        else:
            results = await healthchecker.check_all()

    for result in results:
        if result.status is HealthCheckStatus.HEALTHY:
            noun = "article" if result.item_count == 1 else "articles"
            print(f"{result.slug}: {result.status} ({result.item_count} {noun})")
        else:
            print(f"{result.slug}: {result.status}: {result.error}")
    return int(any(result.status is HealthCheckStatus.UNHEALTHY for result in results))


def _settings_from_args(args: argparse.Namespace) -> Settings:
    defaults = Settings.from_env()
    return Settings(
        data_dir=args.data_dir if args.data_dir is not None else defaults.data_dir,
        host=args.host if args.host is not None else defaults.host,
        port=args.port if args.port is not None else defaults.port,
        refresh_hours=(
            args.refresh_hours if args.refresh_hours is not None else defaults.refresh_hours
        ),
        max_items=defaults.max_items,
        max_concurrency=defaults.max_concurrency,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="scrapiary")
    subparsers = parser.add_subparsers(dest="command", required=True)

    serve = subparsers.add_parser("serve", help="serve feeds and refresh them periodically")
    serve.add_argument("--host")
    serve.add_argument("--port", type=int)
    serve.add_argument("--refresh-hours", type=float)
    serve.add_argument("--data-dir", type=Path)

    refresh = subparsers.add_parser("refresh", help="refresh one or all feeds now")
    refresh.add_argument("site", nargs="?")
    refresh.add_argument("--data-dir", type=Path)
    refresh.set_defaults(host=None, port=None, refresh_hours=None)

    healthcheck = subparsers.add_parser(
        "healthcheck",
        help="check scraper reachability without updating feeds",
    )
    healthcheck.add_argument("site", nargs="?")
    healthcheck.set_defaults(
        host=None,
        port=None,
        refresh_hours=None,
        data_dir=None,
    )

    listing = subparsers.add_parser("list", help="list configured feeds")
    listing.set_defaults(
        host=None,
        port=None,
        refresh_hours=None,
        data_dir=None,
    )
    return parser


def _unreachable(value: object) -> NoReturn:
    raise AssertionError(f"unexpected command: {value}")
