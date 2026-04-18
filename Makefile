.PHONY: install pipx-install pipx-reinstall once dry-run schedule check clean test

CONFIG ?= config.yaml

install:
	uv venv
	uv pip install -e ".[dev]"

test:
	uv run pytest tests/ -v

pipx-install:
	pipx install .

pipx-reinstall:
	pipx reinstall rss_feed_summary

once:
	uv run rss-feed-summary --config $(CONFIG) once

dry-run:
	uv run rss-feed-summary --config $(CONFIG) --dry-run once

schedule:
	uv run rss-feed-summary --config $(CONFIG) schedule

check:
	uv run rss-feed-summary --config $(CONFIG) check

clean:
	uv run rss-feed-summary --config $(CONFIG) clean
