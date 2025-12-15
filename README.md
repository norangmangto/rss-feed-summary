# RSS Feed Summary

Daily job to fetch RSS feeds, summarize items, and email a digest.

## Setup (uv)

Install `uv` if you don't have it:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Create the environment and install deps:

```bash
cd rss_feed_summary
uv venv
uv pip install -e .
```

Optional: activate the venv (paths vary by shell):

```bash
. .venv/bin/activate
```

## Configuration

Edit `config.yaml` (or set `RSS_SUMMARY_CONFIG` env var). Example:

```yaml
feeds:
  - https://hnrss.org/frontpage
  - https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml
limits:
  max_per_feed: 10
  max_sentences: 2
email:
  smtp_host: smtp.example.com
  smtp_port: 587
  username: your_user
  password: your_password
  from: you@example.com
  to: [team@example.com]
  subject: "Daily RSS Summary"
schedule:
  hour: 8
  minute: 0
```

## Usage

Run once:

```bash
uv run rss-feed-summary --config config.yaml once
```

Dry-run (prints email HTML, doesn't send):

```bash
uv run rss-feed-summary --config config.yaml --dry-run once
```

Add date to subject:

```bash
uv run rss-feed-summary --config config.yaml --subject-date once
```

Include plain-text alternative:

```bash
uv run rss-feed-summary --config config.yaml --plain-text once
```

Run the scheduler (keeps running):

```bash
uv run rss-feed-summary --config config.yaml schedule
```

Check feed availability:

```bash
uv run rss-feed-summary --config config.yaml check
```

Clean dead feeds from config (with confirmation):

```bash
uv run rss-feed-summary --config config.yaml clean
```

Clean without confirmation prompt:

```bash
uv run rss-feed-summary --config config.yaml clean --force
```

## macOS Scheduling (launchd)

Copy the provided plist and load it:

```bash
cp launchd/com.example.rss-summary.plist ~/Library/LaunchAgents/
launchctl unload ~/Library/LaunchAgents/com.example.rss-summary.plist 2>/dev/null || true
launchctl load ~/Library/LaunchAgents/com.example.rss-summary.plist
launchctl start com.example.rss-summary
```

Adjust `ProgramArguments` path to `uv` if installed elsewhere.

## Notes

- Summarization is naive; adjust `summarize.py` if you want a different approach.
- HTML is cleaned to text; some feeds may include complex formatting.
- SMTP with TLS is supported; set `use_tls: false` in config to disable.