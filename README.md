# Scrapiary

Scrapiary turns websites without feeds into local RSS 2.0 feeds. It refreshes
sites in the background, stores known items as JSON, and serves only the last
successfully generated XML.

## Run

```console
uv sync
uv run scrapiary serve
```

Feeds are available at:

- <http://127.0.0.1:8765/feeds/0byte.xml>
- <http://127.0.0.1:8765/feeds/abdellatif.xml>
- <http://127.0.0.1:8765/feeds/dottxt.xml>
- <http://127.0.0.1:8765/feeds/claude-blog.xml>
- <http://127.0.0.1:8765/feeds/openai-cookbook.xml>
- <http://127.0.0.1:8765/feeds/jacob-padilla.xml>
- <http://127.0.0.1:8765/feeds/langfuse-changelog.xml>
- <http://127.0.0.1:8765/feeds/parth-sareen.xml>
- <http://127.0.0.1:8765/feeds/claude-cookbook.xml>
- <http://127.0.0.1:8765/feeds/anthropic-engineering.xml>
- <http://127.0.0.1:8765/feeds/humanlayer.xml>
- <http://127.0.0.1:8765/feeds/sunny-bak.xml>
- <http://127.0.0.1:8765/feeds/userjot-engineering.xml>

Useful commands:

```console
make serve
make list
make refresh
make refresh SITE=0byte
make healthcheck
make healthcheck SITE=0byte
```

`scrapiary list` prints every local RSS URL ready to copy into a feed reader.
`scrapiary healthcheck` runs the scrapers without changing stored state or feeds;
it exits nonzero if a scraper fails or returns no articles.

The server binds to localhost and refreshes every six hours by default. Use CLI
options or environment variables to override it:

```console
uv run scrapiary serve --refresh-hours 2 --data-dir ./var/scrapiary
SCRAPIARY_REFRESH_HOURS=2 uv run scrapiary serve
```

Available variables are `SCRAPIARY_REFRESH_HOURS`, `SCRAPIARY_HOST`,
`SCRAPIARY_PORT`, `SCRAPIARY_DATA_DIR`, `SCRAPIARY_MAX_ITEMS`, and
`SCRAPIARY_MAX_CONCURRENCY`.

## Development

```console
uv run pytest
uv run ruff check .
uv run basedpyright
```
