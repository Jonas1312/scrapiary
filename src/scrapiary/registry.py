from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import httpx2

from scrapiary.adapters.scrapers.abdellatif import AbdellatifScraper
from scrapiary.adapters.scrapers.anthropic_engineering import AnthropicEngineeringScraper
from scrapiary.adapters.scrapers.claude_blog import ClaudeBlogScraper
from scrapiary.adapters.scrapers.claude_cookbook import ClaudeCookbookScraper
from scrapiary.adapters.scrapers.dottxt import DotTxtScraper
from scrapiary.adapters.scrapers.humanlayer import HumanLayerScraper
from scrapiary.adapters.scrapers.jacob_padilla import JacobPadillaScraper
from scrapiary.adapters.scrapers.langfuse import LangfuseChangelogScraper
from scrapiary.adapters.scrapers.openai_api_changelog import OpenAIAPIChangelogScraper
from scrapiary.adapters.scrapers.openai_cookbook import OpenAICookbookScraper
from scrapiary.adapters.scrapers.parth_sareen import ParthSareenScraper
from scrapiary.adapters.scrapers.sunny_bak import SunnyBakScraper
from scrapiary.adapters.scrapers.userjot import UserJotEngineeringScraper
from scrapiary.adapters.scrapers.zero_byte import ZeroByteScraper
from scrapiary.ports import Scraper


class ScraperFactory(Protocol):
    def __call__(self, client: httpx2.AsyncClient) -> Scraper: ...


@dataclass(frozen=True, slots=True)
class ScraperDefinition:
    slug: str
    title: str
    home_url: str
    factory: ScraperFactory


SCRAPERS = (
    ScraperDefinition(
        slug=ZeroByteScraper.slug,
        title=ZeroByteScraper.title,
        home_url=ZeroByteScraper.home_url,
        factory=ZeroByteScraper,
    ),
    ScraperDefinition(
        slug=AbdellatifScraper.slug,
        title=AbdellatifScraper.title,
        home_url=AbdellatifScraper.home_url,
        factory=AbdellatifScraper,
    ),
    ScraperDefinition(
        slug=DotTxtScraper.slug,
        title=DotTxtScraper.title,
        home_url=DotTxtScraper.home_url,
        factory=DotTxtScraper,
    ),
    ScraperDefinition(
        slug=ClaudeBlogScraper.slug,
        title=ClaudeBlogScraper.title,
        home_url=ClaudeBlogScraper.home_url,
        factory=ClaudeBlogScraper,
    ),
    ScraperDefinition(
        slug=OpenAICookbookScraper.slug,
        title=OpenAICookbookScraper.title,
        home_url=OpenAICookbookScraper.home_url,
        factory=OpenAICookbookScraper,
    ),
    ScraperDefinition(
        slug=OpenAIAPIChangelogScraper.slug,
        title=OpenAIAPIChangelogScraper.title,
        home_url=OpenAIAPIChangelogScraper.home_url,
        factory=OpenAIAPIChangelogScraper,
    ),
    ScraperDefinition(
        slug=JacobPadillaScraper.slug,
        title=JacobPadillaScraper.title,
        home_url=JacobPadillaScraper.home_url,
        factory=JacobPadillaScraper,
    ),
    ScraperDefinition(
        slug=LangfuseChangelogScraper.slug,
        title=LangfuseChangelogScraper.title,
        home_url=LangfuseChangelogScraper.home_url,
        factory=LangfuseChangelogScraper,
    ),
    ScraperDefinition(
        slug=ParthSareenScraper.slug,
        title=ParthSareenScraper.title,
        home_url=ParthSareenScraper.home_url,
        factory=ParthSareenScraper,
    ),
    ScraperDefinition(
        slug=ClaudeCookbookScraper.slug,
        title=ClaudeCookbookScraper.title,
        home_url=ClaudeCookbookScraper.home_url,
        factory=ClaudeCookbookScraper,
    ),
    ScraperDefinition(
        slug=AnthropicEngineeringScraper.slug,
        title=AnthropicEngineeringScraper.title,
        home_url=AnthropicEngineeringScraper.home_url,
        factory=AnthropicEngineeringScraper,
    ),
    ScraperDefinition(
        slug=HumanLayerScraper.slug,
        title=HumanLayerScraper.title,
        home_url=HumanLayerScraper.home_url,
        factory=HumanLayerScraper,
    ),
    ScraperDefinition(
        slug=SunnyBakScraper.slug,
        title=SunnyBakScraper.title,
        home_url=SunnyBakScraper.home_url,
        factory=SunnyBakScraper,
    ),
    ScraperDefinition(
        slug=UserJotEngineeringScraper.slug,
        title=UserJotEngineeringScraper.title,
        home_url=UserJotEngineeringScraper.home_url,
        factory=UserJotEngineeringScraper,
    ),
)


def build_scrapers(client: httpx2.AsyncClient) -> tuple[Scraper, ...]:
    return tuple(definition.factory(client) for definition in SCRAPERS)
