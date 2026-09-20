.PHONY: format lint pyright test serve refresh healthcheck list

format:
	uv run ruff format .

lint:
	uv run ruff check .

pyright:
	uv run basedpyright

test:
	uv run pytest

serve:
	uv run scrapiary serve

refresh:
	uv run scrapiary refresh $(SITE)

healthcheck:
	uv run scrapiary healthcheck $(SITE)

list:
	uv run scrapiary list
