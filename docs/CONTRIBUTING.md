# Development & Contributing Guide

## Project Structure

```
rss_feed_summary/
├── src/
│   └── rss_feed_summary/
│       ├── __init__.py
│       ├── main.py              # CLI entry point
│       ├── cli.py               # Command handlers
│       ├── config.py            # Config loading
│       ├── fetch.py             # RSS fetching
│       ├── summarize.py         # Text summarization
│       ├── emailer.py           # Email generation & sending
│       ├── health.py            # Feed health checking
│       └── scheduler.py         # Task scheduling
├── templates/
│   └── email.html.j2            # Email template
├── docs/
│   ├── ARCHITECTURE.md          # System design
│   ├── MODULES.md               # Module documentation
│   ├── DATAFLOW.md              # Data flow diagrams
│   ├── CONFIGURATION.md         # Config guide
│   └── CONTRIBUTING.md          # This file
├── launchd/
│   └── com.example.rss-summary.plist  # macOS scheduler config
├── config.yaml                  # Configuration file
├── .gitignore                   # Git ignore rules
├── pyproject.toml               # Project metadata & dependencies
└── README.md                    # Quick start guide
```

## Development Environment

### Setup
```bash
cd rss_feed_summary
uv venv
source .venv/bin/activate
uv pip install -e .
```

### Dependencies
```toml
feedparser      # RSS/Atom parsing
beautifulsoup4  # HTML parsing
jinja2          # Template rendering
pyyaml          # YAML config
requests        # HTTP requests
tenacity        # Retry logic
schedule        # Job scheduling
```

## Code Style

### Conventions
- **Module organization:** One responsibility per module
- **Function length:** < 50 lines preferred
- **Variable names:** Descriptive, snake_case
- **Comments:** For complex logic only (code should be self-documenting)
- **Type hints:** Encouraged for public functions

### Example
```python
def summarize_items(items: List[Dict], max_sentences: int = 3) -> List[Dict]:
    """Generate summaries for RSS items using extractive method."""
    summarized = []
    for item in items:
        # Extract and clean content
        content = item.get("content", "") or item.get("summary", "")
        text = clean_text(content)
        
        # Generate summary
        summary = _extract_summary(text, max_sentences)
        summarized.append({**item, "summary": summary})
    
    return summarized
```

## Testing

### Manual Testing
```bash
# Dry-run without sending
uv run rss-feed-summary --config config.yaml --dry-run once

# With date in subject
uv run rss-feed-summary --config config.yaml --dry-run --subject-date once

# With plain-text alternative
uv run rss-feed-summary --config config.yaml --dry-run --plain-text once

# Check feed health
uv run rss-feed-summary --config config.yaml check

# Verify config
uv run rss-feed-summary --config config.yaml once > /tmp/email.html
# Open /tmp/email.html in browser
```

### Adding Unit Tests
(Currently no test framework configured)

To add pytest:
```bash
uv pip install pytest
```

Example test structure:
```python
# tests/test_summarize.py
import pytest
from rss_feed_summary.summarize import clean_text, extract_sentences

def test_clean_text():
    html = "<p>Hello <b>world</b>!</p>"
    assert clean_text(html) == "Hello world !"

def test_extract_sentences():
    text = "First sentence. Second sentence. A."
    sentences = extract_sentences(text)
    assert len(sentences) == 2  # "A." filtered out (too short)
```

## Making Changes

### Adding a New Feature

#### 1. Plan the change
Document your design in a comment or docstring before coding.

#### 2. Implement with minimal scope
- Change one module at a time
- Keep functions focused
- Preserve backward compatibility

#### 3. Update documentation
- Add docstrings
- Update relevant docs/ files
- Update README if user-facing

#### 4. Test manually
```bash
uv run rss-feed-summary --config config.yaml --dry-run once
```

### Example: Add Email Retry Logic

**File:** `emailer.py`

```python
from tenacity import retry, stop_after_attempt

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
def send_email(...):
    # existing implementation
    with smtplib.SMTP(smtp_host, smtp_port) as server:
        # ...
```

**File:** `docs/MODULES.md`
```markdown
#### `send_email()` (updated)
Now includes automatic retry logic with exponential backoff.
```

## Common Customizations

### Add Support for Markdown Summaries
**File:** `summarize.py`
```python
def render_markdown(items: List[Dict]) -> str:
    """Render items as markdown."""
    lines = []
    for item in items:
        lines.append(f"## {item['title']}")
        lines.append(f"[{item['source']}]({item['link']})")
        lines.append(f"{item['summary']}\n")
    return "\n".join(lines)
```

### Add Database Storage
**File:** `storage.py` (new)
```python
import sqlite3

def save_entries(entries: List[Dict]):
    """Store entries in SQLite for deduplication."""
    conn = sqlite3.connect("entries.db")
    # ...
```

**File:** `fetch.py` (modified)
```python
def collect_entries(...) -> List[Dict]:
    entries = [...]
    # Deduplicate against database
    entries = [e for e in entries if not storage.exists(e["link"])]
    storage.save_entries(entries)
    return entries
```

### Add Slack Integration
**File:** `slack_notifier.py` (new)
```python
import requests

def send_to_slack(items: List[Dict], webhook_url: str):
    """Send summary to Slack channel."""
    message = {
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{item['title']}*\n{item['link']}"
                }
            }
            for item in items
        ]
    }
    requests.post(webhook_url, json=message)
```

**File:** `cli.py` (modified)
```python
if config.get("slack"):
    send_to_slack(summarized, config["slack"]["webhook_url"])
```

## Performance Optimization

### Profiling Feed Fetching
```python
import time

start = time.time()
entries = collect_entries(feeds)
print(f"Fetching took {time.time() - start:.1f}s")
```

### Optimize Summarization
Current: O(n×m²) where n=entries, m=sentences

To improve:
- Cache frequently-scored words
- Use TF-IDF instead of word frequency
- Implement streaming for large feeds

### Optimize Email Rendering
Current: Sequential Jinja2 renders

To improve:
- Cache template compiled form
- Use template caching in Jinja2
- Stream template render for very large lists

## Debugging

### Enable Verbose Output
```python
# In any module
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.debug(f"Fetching {url}")
logger.error(f"Failed: {error}")
```

### Inspect Raw Feed Data
```python
import feedparser
import json

feed = feedparser.parse(url)
print(json.dumps({
    "title": feed.feed.get("title"),
    "entries": len(feed.entries),
    "first_entry": feed.entries[0] if feed.entries else None
}, indent=2, default=str))
```

### Trace Email Rendering
```python
from rss_feed_summary.emailer import render_email

html = render_email(summarized, "Test Subject")
with open("/tmp/email_debug.html", "w") as f:
    f.write(html)
print("Email saved to /tmp/email_debug.html")
```

## Release Checklist

- [ ] Update version in `pyproject.toml`
- [ ] Update `README.md` with new features
- [ ] Update relevant docs/ files
- [ ] Test all commands: `once`, `schedule`, `check`, `clean`
- [ ] Test with dry-run flag
- [ ] Test with real SMTP (or dev server)
- [ ] Verify `.gitignore` is comprehensive
- [ ] Test on macOS (primary platform)
- [ ] Consider testing on Linux

## Resources

- **feedparser docs:** https://www.pythonhosted.org/feedparser/
- **Jinja2 docs:** https://jinja.palletsprojects.com/
- **BeautifulSoup docs:** https://www.crummy.com/software/BeautifulSoup/
- **schedule docs:** https://schedule.readthedocs.io/
- **Python SMTP:** https://docs.python.org/3/library/smtplib.html

## Reporting Issues

When reporting a bug, include:
1. Python version: `python --version`
2. Command run: `uv run rss-feed-summary ...`
3. Error message: Full traceback
4. Config (sanitized): Redact sensitive info
5. OS: macOS version, etc.

## Asking for Help

- Check existing docs/ files first
- Review ARCHITECTURE.md for system overview
- Check MODULES.md for specific function behavior
- Look at similar code for patterns

