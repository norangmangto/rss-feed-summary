# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Python CLI tool that fetches RSS feeds, generates extractive summaries, and emails a daily HTML digest. Managed with `uv`.

## Setup & Common Commands

```bash
# Install dependencies
uv venv && uv pip install -e .

# Run once (fetch, summarize, send email)
uv run rss-feed-summary --config config.yaml once

# Dry-run: renders and prints HTML without sending
uv run rss-feed-summary --config config.yaml --dry-run once

# Check feed health
uv run rss-feed-summary --config config.yaml check

# Remove dead feeds from config.yaml
uv run rss-feed-summary --config config.yaml clean [--force]

# Run the daily scheduler daemon
uv run rss-feed-summary --config config.yaml schedule
```

Config path defaults to `config.yaml` in the working directory; override with `--config` or `RSS_SUMMARY_CONFIG` env var.

## Architecture

The pipeline for the `once` command flows through four independent, single-responsibility modules:

1. **`config.py`** — Loads and validates `config.yaml`. Everything downstream receives the parsed config dict.
2. **`fetch.py`** — Fetches each feed URL via `feedparser`, extracts full article content and thumbnail images, retries with exponential backoff (tenacity, 3 attempts, 1–10s).
3. **`summarize.py`** — Converts HTML to plain text (BeautifulSoup + html2text), scores sentences by word frequency, returns the top N sentences as the summary.
4. **`emailer.py`** — Renders `templates/email.html.j2` (Jinja2) and sends via SMTP/TLS. `--plain-text` adds a `text/plain` alternative part.

Entry point: `main.py` → `cli.py` orchestrates the pipeline. `scheduler.py` wraps `cli.run_once` via the `schedule` library for daemon mode. `health.py` is used only by the `check`/`clean` commands.

## Key Configuration Fields (`config.yaml`)

```yaml
feeds: [list of RSS URLs]
limits:
  max_per_feed: 10       # items fetched per feed
  max_sentences: 2       # sentences per summary
email:
  smtp_host, smtp_port, username, password, from, to, subject
  use_tls: true          # set false to disable TLS
schedule:
  hour: 8
  minute: 0
```

Keep `config.yaml` out of git — it contains SMTP credentials.

## Deduplication

Items from different feeds with identical content are deduplicated before rendering (see commit `ca8d85e`).
