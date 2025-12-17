# Data Flow & Processing

## Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        User Input (CLI)                             │
│                                                                       │
│   uv run rss-feed-summary [--flags] {once|schedule|check|clean}    │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │   main.py       │
                    │ Parse arguments │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
         ┌────▼──┐      ┌────▼──┐    ┌────▼──┐
         │ once  │      │schedule│    │check  │
         │command│      │command │    │command│
         └────┬──┘      └────┬───┘    └────┬──┘
              │              │             │
         ┌────▼──────────────▼──┐      ┌────▼──────────┐
         │  cli.run_once()      │      │health.check() │
         │                      │      │ health.print()│
         └────┬──────────────────┘      └────────────────┘
              │
              ├─────────────────────────────────────┐
              │                                     │
        ┌─────▼──────┐                    ┌────────▼────────┐
        │ config.py  │                    │ scheduler.py    │
        │load_config │                    │run_daily() loop │
        └─────┬──────┘                    └────────┬────────┘
              │                                    │
         ┌────▼─────────────────────────────────────┘
         │
    ┌────▼────────────────────────────────────────┐
    │ fetch.py                                    │
    │ collect_entries(feed_urls)                  │
    └──┬──────────┬──────────┬──────────┬─────────┘
       │          │          │          │
    ┌──▼────┐ ┌──▼────┐ ┌──▼────┐ ┌──▼────┐
    │ Feed1 │ │ Feed2 │ │ Feed3 │ │ Feed4 │
    │(HTTP) │ │(HTTP) │ │(HTTP) │ │(HTTP) │
    └──┬────┘ └──┬────┘ └──┬────┘ └──┬────┘
       │          │         │         │
       └──────────┼─────────┼─────────┘
                  │
         ┌────────▼─────────┐
         │ Parsed Entries   │
         │ [entry1, entry2] │
         │                  │
         │ Each entry has:  │
         │ • title          │
         │ • link           │
         │ • content (HTML) │
         │ • thumbnail URL  │
         │ • source         │
         └────────┬─────────┘
                  │
         ┌────────▼─────────────────┐
         │ summarize.py             │
         │ summarize_items()        │
         └──┬────────┬────────┬─────┘
            │        │        │
      ┌─────▼─┐ ┌────▼───┐ ┌─▼──────┐
      │Clean  │ │Score   │ │Extract │
      │HTML   │ │Sentence│ │Summary │
      └────┬──┘ └────┬───┘ └─┬──────┘
           │         │       │
           └─────────┼───────┘
                     │
         ┌───────────▼────────────┐
         │ Summarized Items       │
         │ [item1, item2, ...]    │
         │                        │
         │ Each item now has:     │
         │ • summary (3 sents)    │
         │ • Plus all prior data  │
         └───────────┬────────────┘
                     │
    ┌────────────────┼─────────────────┐
    │                │                  │
(if --dry-run)  (if not --dry-run)     │
    │                │                  │
┌───▼──┐        ┌────▼──────────────┐   │
│Print │        │ emailer.py        │   │
│HTML  │        │ render_email()    │   │
│stdout│        └────┬─────────────┘   │
└──────┘             │                  │
                ┌────▼────────────────┐ │
                │ Jinja2 Template     │ │
                │ (email.html.j2)     │ │
                │                     │ │
                │ Renders with:       │ │
                │ • Items list        │ │
                │ • Subject           │ │
                │ • CSS styling       │ │
                │ • Thumbnails        │ │
                └────┬────────────────┘ │
                     │                  │
              ┌──────▼─────────────┐    │
              │ HTML Output        │    │
              │ (multipart/mixed)  │    │
              └──────┬─────────────┘    │
                     │                  │
            (if --plain-text)           │
                     │                  │
           ┌─────────▼────────┐         │
           │ render_text()    │         │
           │                  │         │
           │ Plain-text ver.  │         │
           └─────────┬────────┘         │
                     │                  │
         ┌───────────▼──────────┐       │
         │ Final Email Message  │       │
         │ multipart/alternative│       │
         │                      │       │
         │ ├─ text/plain        │       │
         │ └─ text/html         │       │
         └───────────┬──────────┘       │
                     │                  │
                     │<─────────────────┘
                     │
              ┌──────▼───────────┐
              │ emailer.py       │
              │ send_email()     │
              └──┬───────────────┘
                 │
         ┌───────▼────────┐
         │ SMTP Connect   │
         │ (smtp_host:    │
         │  smtp_port)    │
         └───────┬────────┘
                 │
         ┌───────▼────────┐
         │ TLS (if        │
         │ use_tls=True)  │
         └───────┬────────┘
                 │
         ┌───────▼────────────┐
         │ SMTP Authenticate  │
         │ (username/password)│
         └───────┬────────────┘
                 │
         ┌───────▼──────────┐
         │ sendmail()       │
         │ (from/to/message)│
         └───────┬──────────┘
                 │
         ┌───────▼──────────────┐
         │ Email Delivered to   │
         │ Recipient Inbox      │
         └──────────────────────┘
```

## Data Structure Flow

### Entry Structure (after fetch.py)

```python
entry = {
    "title": "How to Use AI",              # str
    "link": "https://example.com/article", # str  
    "published": "Mon, 15 Dec 2025 10:00", # str
    "content": "<p>Full HTML content...</p>", # str (HTML)
    "summary": "Short snippet...",          # str (fallback)
    "thumbnail": "https://example.com/img.jpg", # str (URL or empty)
    "source": "TechCrunch",                 # str (feed name)
    "timestamp": 1702603200.5               # float (unix timestamp)
}
```

### After Summarization

```python
entry = {
    ...  # all above fields preserved
    "summary": "Sentence 1. Sentence 2. Sentence 3."  # updated
}
```

### Rendering Context (for template)

```python
context = {
    "subject": "Daily RSS Summary — 2025-12-15",
    "items": [
        {
            "title": "...",
            "link": "...",
            "published": "...",
            "content": "...",
            "summary": "...",
            "thumbnail": "...",
            "source": "..."
        },
        # ... more items
    ]
}
```

---

## Command-Specific Flows

### Command: `once`

```
Parse args
    ↓
Load config.yaml
    ↓
Fetch RSS feeds
    ├─ For each URL in config["feeds"]
    ├─ HTTP GET with retry (3x)
    ├─ Parse with feedparser
    ├─ Extract content, thumbnail
    ├─ Max N entries per feed
    ↓
Summarize entries
    ├─ Clean HTML from content
    ├─ Split into sentences
    ├─ Score by word frequency
    ├─ Select top 3 sentences
    ↓
Generate email
    ├─ Append date to subject (if --subject-date)
    ├─ Render Jinja2 template → HTML
    ├─ Render text version (if --plain-text)
    ↓
Send/Print
    ├─ If --dry-run: print HTML to stdout
    ├─ Else: connect SMTP, send email
    ↓
Exit
```

### Command: `schedule`

```
Parse args
    ↓
Load config.yaml
    ↓
Extract schedule time
    ├─ config["schedule"]["hour"]
    ├─ config["schedule"]["minute"]
    ↓
Enter run_daily() loop
    ├─ Create schedule (daily at time)
    ├─ Loop forever
    │  ├─ Check every 30s if time to run
    │  ├─ If yes: execute run_once()
    │  └─ Sleep 30s
    ├─ Blocks indefinitely
    ↓
(Process stops on system shutdown or Ctrl+C)
```

### Command: `check`

```
Parse args
    ↓
Load config.yaml
    ↓
Check each feed URL
    ├─ For each URL:
    │  ├─ HTTP HEAD request (5s timeout)
    │  ├─ Capture: status code, response time
    │  ├─ If error: capture error message
    │  ├─ Determine alive = (status < 400)
    ↓
Print report
    ├─ Title and summary (X/Y alive)
    ├─ Each feed with icon (✅ or ❌)
    ├─ Status code and response time
    ├─ Or error message
    ↓
Exit
```

### Command: `clean`

```
Parse args
    ↓
Load config.yaml
    ↓
Check all feed URLs
    ├─ (Same as check command)
    ↓
Identify dead feeds
    ├─ Filter for alive = False
    ↓
Display dead feeds
    ├─ Print list to console
    ↓
Confirm with user
    ├─ If --force: skip
    ├─ Else: prompt "Remove X feeds? (y/n)"
    │  ├─ If no: exit
    ├─ If yes: continue
    ↓
Update config
    ├─ Filter config["feeds"]
    ├─ Remove dead URLs
    ├─ Write back to YAML
    ↓
Report results
    ├─ Old count: 26 feeds
    ├─ Removed: 12 feeds
    ├─ New count: 14 feeds
    ↓
Exit
```

---

## Error Handling Flow

### Feed Fetch Error

```
fetch_feed(url)
    ↓
Attempt 1
    ├─ Timeout? → Retry
    ├─ Connection error? → Retry
    ├─ Success → Return parsed
    ↓
Attempt 2 (if needed, wait 1s)
    ↓
Attempt 3 (if needed, wait 2s)
    ↓
If all fail
    ├─ Exception raised
    ├─ Caught in collect_entries()
    ├─ Feed skipped (no items from it)
    ├─ Continue with next feed
```

### SMTP Send Error

```
send_email(...)
    ↓
Connect to smtp_host:smtp_port
    ├─ If timeout → Raises exception
    ├─ If refused → Raises exception
    ↓
TLS Handshake (if use_tls=True)
    ├─ If failed → Raises exception
    ↓
Authentication (if username/password)
    ├─ If invalid → Raises exception
    ↓
sendmail()
    ├─ If address rejected → Raises exception
    ├─ If server error → Raises exception
    ↓
Success → Message sent
    ↓
All exceptions propagate to caller (cli.py)
Exception handled by main.py catch-all
```

---

## Memory Usage Patterns

### Typical Feed Size
```
Per entry:
- Metadata: ~200 bytes (title, link, source, etc)
- Content: 5-50KB (HTML)
- Thumbnail: ~200 bytes (URL)
─────────────────
Average: ~10KB per entry

Example:
- 20 feeds × 10 entries = 200 entries
- 200 × 10KB = ~2MB in memory
```

### Peak Memory
- Entire entries list in memory during processing
- Summarized entries appended (same data)
- HTML string generated (size = ~2× content)
- Then garbage collected after send

---

## Performance Characteristics

### Fetching
- **Sequential**: O(n) where n = number of feeds
- **Bottleneck**: Slowest feed determines total time
- **Typical**: 10 feeds × 1s average = 10 seconds
- **Retry**: Adds 1-5s per failed feed

### Summarization
- **Per entry**: O(m²) where m = sentences
- **Typical**: 100 entries × 20 sentences = 2000 operations
- **Time**: < 1 second for typical load

### Email Rendering
- **Template render**: ~10ms per entry
- **SMTP connect**: ~100-500ms
- **Send**: ~500-2000ms (depends on server)
- **Total send**: ~1-3 seconds

### Full Pipeline
- Fetch: 10-30 seconds
- Summarize: < 1 second
- Render: 100-500ms
- Send: 1-3 seconds
- **Total: ~12-35 seconds**

---

## State Management

### No Persistent State
- Each run is independent
- No database or state file
- Config file is single source of truth
- All state in memory, released after execution

### Scheduler State
- `schedule` library manages job timing
- Persistent only in running process
- If process dies, needs manual restart
- Consider cron/launchd for reliability

