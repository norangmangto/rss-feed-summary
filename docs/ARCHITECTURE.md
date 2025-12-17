# RSS Feed Summary - Architecture

## System Overview

RSS Feed Summary is a Python-based application that automates the daily process of fetching RSS feeds, generating intelligent summaries, and delivering them via email with rich formatting and thumbnails.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User / Scheduler                        │
│                    (CLI or launchd / cron)                      │
└────────────┬────────────────────────────────────────────────────┘
             │
             ├─────────────────────────────────────────┐
             │                                         │
        ┌────▼──────┐  ┌────────────┐  ┌──────────────┐
        │   once     │  │  schedule  │  │    check     │
        │  (email)   │  │ (daemon)   │  │   (health)   │
        └────┬──────┘  └────────────┘  └──────┬───────┘
             │                                 │
             └──────────────┬──────────────────┘
                            │
                    ┌───────▼────────┐
                    │   config.py    │
                    │  Load YAML cfg │
                    └────────────────┘
                            │
         ┌──────────────────┼──────────────────┐
         │                  │                  │
    ┌────▼─────┐    ┌──────▼──────┐    ┌─────▼──────┐
    │ fetch.py  │    │summarize.py │    │ emailer.py │
    │           │    │             │    │            │
    │ • Extract │    │ • Clean HTML│    │ • Render   │
    │   feeds   │    │ • Score     │    │   template │
    │ • Get     │    │   sentences │    │ • Send     │
    │   content │    │ • Extract   │    │   SMTP     │
    │ • Extract │    │   summary   │    │            │
    │   images  │    │             │    │            │
    └──────────┘    └─────────────┘    └────────────┘
         │                                      │
         └──────────────┬───────────────────────┘
                        │
                 ┌──────▼──────┐
                 │ Template    │
                 │ (Jinja2)    │
                 │             │
                 │ email.html  │
                 │ Renders     │
                 │ items with  │
                 │ thumbnails  │
                 └─────────────┘
                        │
                 ┌──────▼──────┐
                 │   health.py │
                 │  (optional) │
                 │             │
                 │ • Check URL │
                 │ • Report    │
                 │ • Clean     │
                 └─────────────┘
```

## Core Modules

### 1. **config.py** - Configuration Management
- Loads YAML configuration files
- Validates required fields (feeds, email settings)
- Provides defaults for optional settings

### 2. **fetch.py** - RSS Feed Retrieval
- Uses `feedparser` to fetch and parse RSS feeds
- Extracts full article content (not just summaries)
- Identifies and extracts thumbnail images from various RSS formats
- Implements retry logic with exponential backoff

### 3. **summarize.py** - Intelligent Summarization
- Converts HTML to clean text
- Implements extractive summarization using word frequency scoring
- Selects most important sentences based on keyword prominence
- Configurable summary length (default: 3 sentences)

### 4. **emailer.py** - Email Generation & Sending
- Renders HTML emails using Jinja2 templates
- Generates plain-text alternatives for email clients
- Sends emails via SMTP with TLS support
- Supports custom subject lines and formatting

### 5. **health.py** - Feed Health Checking
- Tests RSS feed URLs for availability
- Reports HTTP status codes and response times
- Identifies dead feeds for cleanup
- Provides summary statistics

### 6. **scheduler.py** - Task Scheduling
- Runs jobs on daily schedule
- Integrates with `schedule` library
- Blocks execution until scheduled time

### 7. **cli.py** - Command Orchestration
- Coordinates module interactions
- Handles `once`, `schedule`, `check`, and `clean` commands
- Manages flags (dry-run, subject-date, plain-text)

### 8. **main.py** - Entry Point
- Parses command-line arguments
- Routes to appropriate CLI function
- Provides help documentation

## Data Flow

```
Config YAML
    │
    ├─> Feed URLs ─┐
    │              │
    │              ▼
    │         fetch.py (HTTP requests)
    │              │
    │              ├─> Raw entries
    │              ├─> Full content
    │              └─> Thumbnails
    │
    ├─> Email Settings
    │
    ▼
  CLI Handler
    │
    ├─> Collect entries
    ├─> Summarize content
    ├─> Render template
    ├─> Send email (or print in dry-run)
    │
    ▼
  Email (HTML + Text)
    │
    └─> Recipient inbox
```

## Processing Pipeline

For the `once` command:

1. **Load Configuration** → Parse config.yaml
2. **Fetch Feeds** → Download RSS feeds, extract content & thumbnails
3. **Summarize** → Clean HTML, score sentences, extract key content
4. **Render Email** → Fill Jinja2 template with items
5. **Send** → Connect to SMTP, deliver email

For the `check` command:

1. **Load Configuration** → Parse config.yaml
2. **Health Check** → Test each feed URL
3. **Report** → Display status with visual indicators

For the `clean` command:

1. **Load Configuration** → Parse config.yaml
2. **Health Check** → Test each feed URL
3. **Filter** → Identify dead feeds
4. **Update** → Write cleaned list back to YAML

## Design Patterns

### Separation of Concerns
- **Fetching** (fetch.py): Only retrieves and extracts data
- **Processing** (summarize.py): Only summarizes content
- **Delivery** (emailer.py): Only handles email formatting & sending
- **Health** (health.py): Isolated health checking logic

### Retry Logic
- `fetch.py` uses tenacity for resilient RSS fetching
- Exponential backoff (1s → 10s) with 3 attempts

### Configuration-Driven
- All settings in YAML, no hardcoding
- Sensible defaults for optional fields
- Environment variable override support

### Template-Based Rendering
- Jinja2 for flexible email formatting
- Plain-text and HTML alternatives supported
- Easy to customize appearance

## Extension Points

### Add New Summarization Algorithm
Modify `summarize.py`:
- Replace `score_sentences()` with your algorithm
- Implement different scoring metrics (TF-IDF, sentiment, etc.)

### Add New Output Format
Extend `emailer.py`:
- Create new template (Slack, Markdown, etc.)
- Modify `render_email()` to support new formats

### Add Feed Authentication
Extend `fetch.py`:
- Support HTTP Basic Auth in config
- Add OAuth token support

### Custom Scheduling
Modify `scheduler.py`:
- Integrate with APScheduler for cron expressions
- Add timezone support

## Dependencies

| Module | Purpose |
|--------|---------|
| feedparser | RSS/Atom feed parsing |
| beautifulsoup4 | HTML parsing and cleaning |
| jinja2 | Email template rendering |
| pyyaml | YAML configuration loading |
| requests | HTTP requests for health checking |
| tenacity | Retry logic for failed requests |
| schedule | Daily job scheduling |

## Performance Considerations

- **Feed fetching**: Sequential (slow feeds won't block others much with retries)
- **Summarization**: O(n*m) where n=items, m=avg sentences per item
- **Email sending**: Single SMTP connection, sequential sending
- **Memory**: All entries loaded in memory; for large feeds (>1000 items), consider pagination

## Error Handling

- **Feed fetch failures**: Logged, retried 3x, item skipped if all fail
- **SMTP errors**: Raised to caller (caught in main)
- **Missing thumbnails**: Gracefully omitted from email
- **Malformed YAML**: Validation error on load, process aborts

## Security

- SMTP credentials stored in config.yaml (keep out of git!)
- Use `.gitignore` to exclude config files with secrets
- No credential logging
- HTTPS for all external requests
- TLS for SMTP connections
