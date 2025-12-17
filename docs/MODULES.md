# Module Documentation

## config.py

### Purpose
Loads and validates the YAML configuration file. Acts as the single source of truth for all application settings.

### Functions

#### `load_config(path: str | None) -> Dict[str, Any]`
Load and validate configuration from YAML file.

**Parameters:**
- `path`: Path to config.yaml. If None, uses `RSS_SUMMARY_CONFIG` env var or default path.

**Returns:**
Dictionary with keys: `feeds`, `limits`, `email`, `schedule`

**Validation:**
- `feeds` must be a non-empty list of URLs
- `email.smtp_host` is required
- `email.from` and `email.to` are required
- Raises `ValueError` if validation fails

**Example:**
```python
cfg = load_config("config.yaml")
feeds = cfg["feeds"]  # List of feed URLs
smtp_host = cfg["email"]["smtp_host"]
```

---

## fetch.py

### Purpose
Downloads RSS feeds, extracts article content, and identifies thumbnail images.

### Functions

#### `fetch_feed(url: str) -> Dict[str, Any]`
Fetch and parse a single RSS feed with retry logic.

**Parameters:**
- `url`: RSS feed URL

**Returns:**
Parsed feed object from feedparser

**Behavior:**
- Retries up to 3 times on failure
- Uses exponential backoff (1s, 2s, 4s, etc.)
- Catches and retries on timeout/connection errors

#### `extract_thumbnail(entry: Dict[str, Any]) -> str`
Extract image URL from various RSS entry fields.

**Checks (in order):**
1. `media_thumbnail` - Media RSS namespace
2. `media_content` with `medium="image"` - Media RSS content
3. `enclosures` with MIME type `image/*` - RSS enclosures
4. `links` with `rel="enclosure"` and MIME type `image/*` - Standard links

**Returns:**
Image URL string, or empty string if no image found

**Example:**
```python
# RSS with thumbnail
entry = {
    "title": "Article",
    "media_thumbnail": [{"url": "https://example.com/image.jpg"}]
}
url = extract_thumbnail(entry)  # Returns "https://example.com/image.jpg"
```

#### `collect_entries(feed_urls: List[str], max_per_feed: int = 10) -> List[Dict[str, Any]]`
Fetch all feeds and extract entries with content and thumbnails.

**Parameters:**
- `feed_urls`: List of RSS feed URLs
- `max_per_feed`: Maximum entries per feed (default: 10)

**Returns:**
List of entry dictionaries with keys:
- `title`: Article title
- `link`: Article URL
- `published`: Publication date
- `content`: Full article HTML (if available)
- `summary`: Short summary (fallback)
- `thumbnail`: Image URL (empty if not available)
- `source`: Feed name
- `timestamp`: When fetched

**Data Sources (priority):**
1. `entry["content"][0]["value"]` - Full article content
2. `entry["summary_detail"]["value"]` - Detailed summary
3. `entry["summary"]` - Basic summary
4. Empty string if none available

**Example:**
```python
entries = collect_entries(
    ["https://example.com/feed.xml", "https://another.com/rss"],
    max_per_feed=5
)
# Returns list of 10 entries (max 5 per feed)
```

---

## summarize.py

### Purpose
Converts HTML to plain text and generates intelligent summaries using extractive summarization.

### Functions

#### `clean_text(html: str) -> str`
Convert HTML to clean plain text.

**Parameters:**
- `html`: HTML string (may contain tags, entities, etc.)

**Process:**
1. Parse HTML with BeautifulSoup
2. Extract text (preserves structure with spaces)
3. Collapse multiple whitespaces to single space
4. Strip leading/trailing whitespace

**Returns:**
Clean text string

**Example:**
```python
html = "<p>Hello <b>world</b>!</p>"
text = clean_text(html)  # Returns "Hello world !"
```

#### `extract_sentences(text: str) -> List[str]`
Split text into sentences, filtering out very short ones.

**Parameters:**
- `text`: Plain text string

**Process:**
1. Split on sentence boundaries (`.`, `!`, `?`)
2. Strip whitespace from each sentence
3. Filter out sentences < 20 characters (noise)

**Returns:**
List of sentence strings

**Example:**
```python
text = "This is great. Very good. A."
sentences = extract_sentences(text)  
# Returns ["This is great.", "Very good."]
```

#### `score_sentences(sentences: List[str]) -> List[tuple]`
Score sentences by word frequency importance.

**Algorithm:**
1. Extract words ≥ 4 characters from all sentences
2. Count word frequency across all sentences
3. Score each sentence by sum of word frequencies
4. Normalize by sentence word count

**Returns:**
List of tuples: `(score, original_index, sentence_text)`
Sorted by score (highest first), preserving original order as tiebreaker

**Example:**
```python
sentences = [
    "Machine learning is powerful",
    "AI uses machine learning",
    "Learning is important"
]
scored = score_sentences(sentences)
# scored[0] might be ("AI uses machine learning", ...)
# because "machine" and "learning" have high frequency
```

#### `summarize_items(items: List[Dict], max_sentences: int = 3) -> List[Dict]`
Generate summaries for all items using extractive summarization.

**Parameters:**
- `items`: List of entry dictionaries (from `fetch.py`)
- `max_sentences`: Maximum sentences in summary (default: 3)

**Process:**
1. Extract full content from item (or use fallback summary)
2. Clean HTML to text
3. Split into sentences
4. If ≤ max_sentences: use all (natural summary)
5. If > max_sentences: score and select top sentences
6. Preserve original sentence order in summary

**Returns:**
List of items with new `summary` field containing generated summary

**Example:**
```python
items = [{
    "title": "Article",
    "content": "<p>Lorem ipsum...</p>",
    "summary": ""
}]
summarized = summarize_items(items, max_sentences=2)
# summarized[0]["summary"] = "Sentence 1. Sentence 3."
```

---

## emailer.py

### Purpose
Renders email templates and sends via SMTP with HTML and plain-text alternatives.

### Functions

#### `render_email(items: List[Dict], subject: str, template_dir: str = "templates") -> str`
Render HTML email from Jinja2 template.

**Parameters:**
- `items`: List of entries to include
- `subject`: Email subject line
- `template_dir`: Directory containing templates (default: "templates")

**Template Variables:**
- `items`: List of item dicts with all fields
- `subject`: Subject string

**Returns:**
Rendered HTML string

**Process:**
1. Create Jinja2 environment with autoescape
2. Load `email.html.j2` template
3. Render with context data

**Example:**
```python
items = [{"title": "News", "link": "...", "summary": "..."}]
html = render_email(items, "Daily Summary")
```

#### `render_text(items: List[Dict], subject: str) -> str`
Generate plain-text version of email.

**Parameters:**
- `items`: List of entries
- `subject`: Email subject

**Returns:**
Plain-text string with entries formatted as:
```
Daily Summary

• Title
  Source Published
  URL
  Summary

```

**Purpose:**
Email clients that don't support HTML still get readable format.

#### `send_email(html_body: str, smtp_host: str, smtp_port: int, username: str | None, password: str | None, mail_from: str, mail_to: List[str], subject: str, use_tls: bool = True, text_body: str | None = None)`
Send email via SMTP with HTML and optional plain-text alternative.

**Parameters:**
- `html_body`: HTML email content
- `smtp_host`: SMTP server address
- `smtp_port`: SMTP port (typically 587 or 465)
- `username`: SMTP username (optional)
- `password`: SMTP password (optional)
- `mail_from`: From address
- `mail_to`: List of recipient addresses
- `subject`: Email subject
- `use_tls`: Enable TLS encryption (default: True)
- `text_body`: Plain-text alternative (optional)

**Process:**
1. Create multipart/alternative message
2. Attach plain-text version (if provided)
3. Attach HTML version
4. Connect to SMTP server
5. Enable TLS if requested
6. Authenticate if credentials provided
7. Send message

**Multipart Structure:**
```
multipart/alternative
├── text/plain (if text_body provided)
└── text/html
```

Email clients show HTML, fall back to plain-text if needed.

**Example:**
```python
send_email(
    html_body=html,
    text_body=text,
    smtp_host="smtp.gmail.com",
    smtp_port=587,
    username="user@gmail.com",
    password="app_password",
    mail_from="you@example.com",
    mail_to=["recipient@example.com"],
    subject="Daily Summary",
    use_tls=True
)
```

---

## health.py

### Purpose
Tests RSS feed URLs for availability and provides cleanup utilities.

### Functions

#### `check_single_url(url: str, timeout: int = 5) -> Dict`
Check a single URL's health status.

**Parameters:**
- `url`: Feed URL to check
- `timeout`: Timeout in seconds (default: 5)

**Returns:**
Dictionary with keys:
- `url`: Original URL
- `alive`: Boolean (status < 400)
- `status_code`: HTTP status code (or None)
- `response_time_ms`: Response time in milliseconds (or None)
- `error`: Error message (or None)

**Status Determination:**
- `alive=True`: HTTP 2xx or 3xx (success or redirect)
- `alive=False`: HTTP 4xx, 5xx, or connection error

**Example:**
```python
result = check_single_url("https://example.com/feed.xml")
# Returns:
# {
#     "url": "https://example.com/feed.xml",
#     "alive": True,
#     "status_code": 200,
#     "response_time_ms": 234.5,
#     "error": None
# }
```

#### `check_feed_health(feed_urls: List[str], timeout: int = 5) -> List[Dict]`
Check health of all feeds.

**Parameters:**
- `feed_urls`: List of feed URLs
- `timeout`: Timeout per URL (default: 5)

**Returns:**
List of status dictionaries (one per feed)

#### `print_health_report(results: List[Dict])`
Print formatted health report to stdout.

**Output Format:**
```
📊 RSS Feed Health Report
════════════════════════════════════════════════════════════════════════════════
Status: 14/26 feeds are healthy

✅ https://example.com/feed (alive)
   Status: 200 | Response time: 234.5ms
❌ https://dead.com/rss (dead)
   Error: Connection timeout after 5s
```

#### `get_dead_feeds(results: List[Dict]) -> List[str]`
Extract list of dead feed URLs from health check results.

**Parameters:**
- `results`: List from `check_feed_health()`

**Returns:**
List of URLs where `alive=False`

**Example:**
```python
results = check_feed_health(urls)
dead = get_dead_feeds(results)  # ["https://dead1.com", "https://dead2.com"]
```

---

## scheduler.py

### Purpose
Simple daily job scheduler using the `schedule` library.

### Functions

#### `run_daily(hour: int, minute: int, job: Callable[[], None])`
Schedule and run a job daily at specified time.

**Parameters:**
- `hour`: Hour (0-23)
- `minute`: Minute (0-59)
- `job`: Callable function to run

**Behavior:**
- Creates a daily schedule
- Blocks indefinitely
- Checks every 30 seconds if job should run
- Runs job at specified time
- Repeats daily

**Example:**
```python
def my_job():
    print("Running at 8:00 AM daily")

run_daily(8, 0, my_job)  # Blocks until system shutdown
```

---

## cli.py

### Purpose
Orchestrates module interactions for each CLI command.

### Functions

#### `check_feeds(config_path: Optional[str] = None)`
Health check command handler.

**Process:**
1. Load config
2. Check all feed URLs
3. Print health report

#### `clean_feeds(config_path: Optional[str] = None, force: bool = False)`
Clean dead feeds command handler.

**Process:**
1. Load config
2. Check all feed URLs
3. List dead feeds
4. Prompt user (unless `--force`)
5. Write cleaned config back to YAML
6. Report results

**Output:**
- Lists dead feeds before deletion
- Confirms with user
- Reports before/after counts

#### `run_once(config_path: Optional[str] = None, dry_run: bool = False, subject_date: bool = False, plain_text: bool = False)`
Fetch, summarize, and send email (once).

**Parameters:**
- `config_path`: Path to config.yaml
- `dry_run`: Print email instead of sending
- `subject_date`: Append date to subject
- `plain_text`: Include text/plain alternative

**Process:**
1. Load config
2. Fetch feeds
3. Summarize entries
4. Optionally append date to subject
5. Render email template
6. If plain_text: render text alternative
7. If dry_run: print HTML to stdout
8. Else: send via SMTP

#### `run_scheduler(config_path: Optional[str] = None)`
Schedule daemon command handler.

**Process:**
1. Load config
2. Extract schedule time from config
3. Call `run_daily()` with `run_once` as job
4. Block indefinitely

---

## main.py

### Purpose
CLI entry point and argument parsing.

### Functions

#### `main()`
Parse arguments and dispatch to CLI handler.

**Arguments:**
- `--config`: Path to config.yaml (optional)
- `--dry-run`: Print email instead of sending
- `--subject-date`: Append date to subject
- `--plain-text`: Include plain-text alternative
- Command: `once`, `schedule`, `check`, `clean`

**Command Handlers:**
- `once`: Send email once (default if no command)
- `schedule`: Run daily scheduler
- `check`: Check feed health
- `clean`: Remove dead feeds (with optional `--force`)

**Example:**
```bash
rss-feed-summary --config config.yaml once
rss-feed-summary --config config.yaml --dry-run once
rss-feed-summary --config config.yaml schedule
rss-feed-summary --config config.yaml check
rss-feed-summary --config config.yaml clean --force
```
