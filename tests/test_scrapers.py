from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import httpx2
import pytest

from scrapiary.adapters.scrapers.abdellatif import AbdellatifScraper
from scrapiary.adapters.scrapers.anthropic_engineering import AnthropicEngineeringScraper
from scrapiary.adapters.scrapers.claude_blog import ClaudeBlogScraper
from scrapiary.adapters.scrapers.claude_cookbook import ClaudeCookbookScraper
from scrapiary.adapters.scrapers.common import canonicalize_url
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

FIXTURES = Path(__file__).parent / "fixtures"


def fixture_client(filename: str) -> httpx2.AsyncClient:
    html = (FIXTURES / filename).read_text(encoding="utf-8")

    return html_client(html)


def html_client(html: str) -> httpx2.AsyncClient:
    async def handler(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(200, text=html, request=request)

    return httpx2.AsyncClient(transport=httpx2.MockTransport(handler))


def test_canonicalize_url_removes_only_known_tracking_parameters() -> None:
    result = canonicalize_url(
        "https://Example.COM/blog/",
        "../post?id=42&utm_source=email&custom=yes#comments",
    )

    assert result == "https://example.com/post?id=42&custom=yes"


@pytest.mark.asyncio
async def test_zero_byte_scraper_enriches_listing_items_from_article_pages() -> None:
    pages = {
        "https://0byte.io/": "0byte.html",
        "https://0byte.io/articles/new.html": "0byte_new_article.html",
        "https://0byte.io/articles/older.html?id=42": "0byte_older_article.html",
    }

    async def handler(request: httpx2.Request) -> httpx2.Response:
        filename = pages[str(request.url)]
        html = (FIXTURES / filename).read_text(encoding="utf-8")
        return httpx2.Response(200, text=html, request=request)

    async with httpx2.AsyncClient(transport=httpx2.MockTransport(handler)) as client:
        items = await ZeroByteScraper(client).scrape()

    assert [item.title for item in items] == ["New article", "Older article"]
    assert [item.url for item in items] == [
        "https://0byte.io/articles/new.html",
        "https://0byte.io/articles/older.html?id=42",
    ]
    assert items[0].published_at == datetime(2026, 5, 7, tzinfo=UTC)
    assert items[0].description == (
        "This is the useful introduction to the new article. It becomes the feed summary."
    )
    assert items[1].published_at == datetime(2025, 1, 21, tzinfo=UTC)
    assert items[1].description == "The older article summary."


@pytest.mark.asyncio
async def test_abdellatif_scraper_extracts_articles() -> None:
    async with fixture_client("abdellatif.html") as client:
        items = await AbdellatifScraper(client).scrape()

    assert [item.title for item in items] == [
        "The Next Coding Interface is a Canvas",
        "Hackable Software",
    ]
    assert items[0].url == "https://blog.abdellatif.io/the-next-coding-interface-is-a-canvas"
    assert items[0].published_at == datetime(2026, 3, 6, tzinfo=UTC)
    assert items[0].author == "Abdellatif Abdelfattah"


@pytest.mark.asyncio
async def test_dottxt_scraper_extracts_articles() -> None:
    async with fixture_client("dottxt.html") as client:
        items = await DotTxtScraper(client).scrape()

    assert [item.title for item in items] == ["A new post", "An older post"]
    assert items[0].url == "https://blog.dottxt.ai/new-post.html"
    assert items[0].published_at == datetime(2026, 6, 22, tzinfo=UTC)
    assert items[0].author == ".txt team"


@pytest.mark.asyncio
async def test_claude_blog_scraper_extracts_grid_without_hero_duplicates() -> None:
    async with fixture_client("claude_blog.html") as client:
        items = await ClaudeBlogScraper(client).scrape()

    assert [item.title for item in items] == ["A new Claude post", "An older Claude post"]
    assert items[0].url == "https://claude.com/blog/new-post"
    assert items[0].published_at == datetime(2026, 9, 17, tzinfo=UTC)
    assert items[0].author == "Anthropic"


@pytest.mark.asyncio
async def test_openai_cookbook_scraper_extracts_recipe_list_without_featured_duplicates() -> None:
    async with fixture_client("openai_cookbook.html") as client:
        items = await OpenAICookbookScraper(client).scrape()

    assert [item.title for item in items] == ["A new recipe", "An older recipe"]
    assert items[0].url == "https://developers.openai.com/cookbook/examples/new-recipe"
    assert items[0].published_at == datetime(2026, 9, 14, tzinfo=UTC)


@pytest.mark.asyncio
async def test_openai_api_changelog_scraper_keeps_entry_content_and_same_day_items() -> None:
    async with fixture_client("openai_api_changelog.html") as client:
        items = await OpenAIAPIChangelogScraper(client).scrape()

    assert [item.title for item in items] == [
        "Feature: Released GPT-6 Sol and GPT-6 Luna.",
        "Update: Added API key expiration controls.",
    ]
    assert [item.published_at for item in items] == [
        datetime(2026, 9, 22, tzinfo=UTC),
        datetime(2026, 9, 22, tzinfo=UTC),
    ]
    assert items[0].url != items[1].url
    assert items[0].url.startswith(
        "https://developers.openai.com/api/docs/changelog#2026-09-22-"
    )
    assert items[0].description == (
        '<p>Released <a href="https://developers.openai.com/api/docs/models/gpt-6-sol">'
        "GPT-6 Sol</a> and GPT-6 Luna.</p><ul><li>Text and image input</li></ul>"
    )
    assert items[0].author == "OpenAI"


@pytest.mark.asyncio
async def test_jacob_padilla_scraper_reads_exact_dates_from_articles() -> None:
    pages = {
        "https://jacobpadilla.com/writing": """
            <ul><li class="writing-entry">
              <a href="/writing/asyncio-protocols">Asyncio protocols</a>
            </li></ul>
        """,
        "https://jacobpadilla.com/writing/asyncio-protocols": """
            <p>Posted on <time datetime="2025-07-01T19:23:44Z">July 1, 2025</time></p>
        """,
    }

    async def handler(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(200, text=pages[str(request.url)], request=request)

    async with httpx2.AsyncClient(transport=httpx2.MockTransport(handler)) as client:
        items = await JacobPadillaScraper(client).scrape()

    assert items[0].title == "Asyncio protocols"
    assert items[0].published_at == datetime(2025, 7, 1, 19, 23, 44, tzinfo=UTC)


@pytest.mark.asyncio
async def test_langfuse_scraper_uses_dates_from_canonical_paths() -> None:
    html = """
      <a class="group relative" href="/changelog/2026-09-07-evaluator-backfills">
        <h3>Run evaluators on historical observations</h3>
      </a>
    """
    async with html_client(html) as client:
        items = await LangfuseChangelogScraper(client).scrape()

    assert items[0].url == ("https://langfuse.com/changelog/2026-09-07-evaluator-backfills")
    assert items[0].published_at == datetime(2026, 9, 7, tzinfo=UTC)


@pytest.mark.asyncio
async def test_parth_sareen_scraper_combines_section_year_and_item_date() -> None:
    html = """
      <section class="year-section" data-year="2025">
        <a class="writings-item" href="/writings/sampling/">
          <span class="writings-item-date">Sep 10</span>
          <span class="writings-item-title">Sampling and structured outputs</span>
          <p class="writings-item-dek">What sampling actually does.</p>
        </a>
      </section>
    """
    async with html_client(html) as client:
        items = await ParthSareenScraper(client).scrape()

    assert items[0].published_at == datetime(2025, 9, 10, tzinfo=UTC)
    assert items[0].description == "What sampling actually does."


@pytest.mark.asyncio
async def test_claude_cookbook_scraper_enriches_monthly_rows_with_exact_dates() -> None:
    pages = {
        "https://platform.claude.com/cookbook/": """
          <table><tbody><tr>
            <td>
              <a href="/cookbook/scheduled-reviewer"></a>
              <span class="font-medium text-primary">Build a scheduled reviewer</span>
              <p class="text-body">A read-only review agent.</p>
            </td>
          </tr></tbody></table>
        """,
        "https://platform.claude.com/cookbook/scheduled-reviewer": """
          <header>
            <img alt="Cody Anthony">
            <div class="text-body text-muted">Published on August 26, 2026</div>
          </header>
        """,
    }

    async def handler(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(200, text=pages[str(request.url)], request=request)

    async with httpx2.AsyncClient(transport=httpx2.MockTransport(handler)) as client:
        items = await ClaudeCookbookScraper(client).scrape()

    assert items[0].published_at == datetime(2026, 8, 26, tzinfo=UTC)
    assert items[0].author == "Cody Anthony"
    assert items[0].description == "A read-only review agent."


@pytest.mark.asyncio
async def test_anthropic_engineering_enriches_featured_article_date() -> None:
    pages = {
        "https://www.anthropic.com/engineering": """
          <article class="ArticleList_featured">
            <a href="/engineering/how-we-contain-claude">
              <h2>How we contain Claude</h2>
              <p class="ArticleList_summary">How Anthropic limits blast radius.</p>
            </a>
          </article>
          <article class="ArticleList_article">
            <a href="/engineering/managed-agents">
              <h3>Scaling Managed Agents</h3>
              <div class="ArticleList_date">Apr 08, 2026</div>
            </a>
          </article>
        """,
        "https://www.anthropic.com/engineering/how-we-contain-claude": """
          <p class="HeroEngineering_date">Published May 25, 2026</p>
        """,
    }

    async def handler(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(200, text=pages[str(request.url)], request=request)

    async with httpx2.AsyncClient(transport=httpx2.MockTransport(handler)) as client:
        items = await AnthropicEngineeringScraper(client).scrape()

    assert [item.published_at for item in items] == [
        datetime(2026, 5, 25, tzinfo=UTC),
        datetime(2026, 4, 8, tzinfo=UTC),
    ]


@pytest.mark.asyncio
async def test_humanlayer_scraper_extracts_metadata_and_summary() -> None:
    html = """
      <a class="block py-2 group" href="/blog/show-me-skill">
        <h2>show-me</h2>
        <p class="text-sm">Dex · August 12, 2026 · 7 min read</p>
        <div><p>A coding-agent skill for compact visuals.</p></div>
      </a>
    """
    async with html_client(html) as client:
        items = await HumanLayerScraper(client).scrape()

    assert items[0].published_at == datetime(2026, 8, 12, tzinfo=UTC)
    assert items[0].author == "Dex"
    assert items[0].description == "A coding-agent skill for compact visuals."


@pytest.mark.asyncio
async def test_sunny_bak_scraper_extracts_real_dates() -> None:
    html = """
      <div class="post-list"><a href="/blog/schemas">
        <p>August 7, 2026</p><p>Standardizing AI Observability</p>
      </a></div>
    """
    async with html_client(html) as client:
        items = await SunnyBakScraper(client).scrape()

    assert items[0].published_at == datetime(2026, 8, 7, tzinfo=UTC)


@pytest.mark.asyncio
async def test_userjot_scraper_keeps_only_engineering_posts() -> None:
    html = """
      <ul>
        <li><a href="/blog/pgvector-deep-dive">
          <div><span>Engineering</span><time datetime="2025-01-19">Jan 19</time></div>
          <h2>Deep Dive into Vector Similarity Search</h2><p>A pgvector guide.</p>
        </a></li>
        <li><a href="/blog/feedback-board">
          <div><span>Product</span><time datetime="2026-02-08">Feb 8</time></div>
          <h2>What Is a Feedback Board?</h2>
        </a></li>
      </ul>
    """
    async with html_client(html) as client:
        items = await UserJotEngineeringScraper(client).scrape()

    assert [item.title for item in items] == ["Deep Dive into Vector Similarity Search"]
    assert items[0].published_at == datetime(2025, 1, 19, tzinfo=UTC)


@pytest.mark.asyncio
async def test_scraper_fails_when_an_article_has_no_publication_date() -> None:
    html = """
        <div class="blog_cms_grid">
          <div class="blog_cms_item">
            <div class="card_blog_title">Undated article</div>
            <a data-cta-position="Blog grid" href="/blog/undated">Read more</a>
          </div>
        </div>
    """
    async with html_client(html) as client:
        with pytest.raises(RuntimeError, match="publication date not found"):
            await ClaudeBlogScraper(client).scrape()


@pytest.mark.asyncio
async def test_scraper_reports_a_layout_change_instead_of_publishing_an_empty_feed() -> None:
    async with html_client("<html><body>No articles here</body></html>") as client:
        with pytest.raises(RuntimeError, match="page layout may have changed"):
            await ZeroByteScraper(client).scrape()
