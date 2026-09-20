from __future__ import annotations

import sys

import pytest

import scrapiary.cli as cli
from scrapiary.application import HealthCheckResult, HealthCheckStatus
from scrapiary.registry import SCRAPERS


class FakeHttpClient:
    async def __aenter__(self) -> FakeHttpClient:
        return self

    async def __aexit__(self, *args: object) -> None:
        pass


class FakeHealthchecker:
    def __init__(self, results: tuple[HealthCheckResult, ...]) -> None:
        self._results = results

    async def check_all(self) -> tuple[HealthCheckResult, ...]:
        return self._results

    async def check(self, slug: str) -> HealthCheckResult:
        for result in self._results:
            if result.slug == slug:
                return result
        raise KeyError(f"unknown scraper: {slug}")


def test_list_prints_local_rss_urls(monkeypatch, capsys) -> None:
    monkeypatch.setattr(sys, "argv", ["scrapiary", "list"])
    monkeypatch.setenv("SCRAPIARY_HOST", "127.0.0.1")
    monkeypatch.setenv("SCRAPIARY_PORT", "8765")

    cli.main()

    local_urls = [f"http://127.0.0.1:8765/feeds/{definition.slug}.xml" for definition in SCRAPERS]
    assert capsys.readouterr().out.splitlines() == local_urls


def test_healthcheck_prints_results_and_exits_nonzero_when_a_scraper_is_unhealthy(
    monkeypatch,
    capsys,
) -> None:
    checker = FakeHealthchecker(
        (
            HealthCheckResult("healthy", HealthCheckStatus.HEALTHY, item_count=3),
            HealthCheckResult(
                "broken",
                HealthCheckStatus.UNHEALTHY,
                error="website unavailable",
            ),
        )
    )
    monkeypatch.setattr(sys, "argv", ["scrapiary", "healthcheck"])
    monkeypatch.setattr(cli, "build_http_client", FakeHttpClient)
    monkeypatch.setattr(cli, "build_healthchecker", lambda _client, _settings: checker)

    with pytest.raises(SystemExit) as exit_info:
        cli.main()

    assert exit_info.value.code == 1
    assert capsys.readouterr().out.splitlines() == [
        "healthy: healthy (3 articles)",
        "broken: unhealthy: website unavailable",
    ]


def test_healthcheck_unknown_scraper_exits_with_code_two(monkeypatch, capsys) -> None:
    checker = FakeHealthchecker(())
    monkeypatch.setattr(sys, "argv", ["scrapiary", "healthcheck", "missing"])
    monkeypatch.setattr(cli, "build_http_client", FakeHttpClient)
    monkeypatch.setattr(cli, "build_healthchecker", lambda _client, _settings: checker)

    with pytest.raises(SystemExit) as exit_info:
        cli.main()

    assert exit_info.value.code == 2
    assert capsys.readouterr().out.strip() == "unknown scraper: missing"
