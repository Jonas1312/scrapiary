from __future__ import annotations

from scrapiary.config import Settings


def test_refresh_interval_defaults_to_six_hours() -> None:
    assert Settings().refresh_hours == 6


def test_refresh_interval_can_be_configured(monkeypatch) -> None:
    monkeypatch.setenv("SCRAPIARY_REFRESH_HOURS", "2.5")

    assert Settings.from_env().refresh_hours == 2.5
