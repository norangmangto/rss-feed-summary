# Documentation Index

Welcome to the RSS Feed Summary documentation. This guide helps you understand, configure, and extend the application.

## Quick Navigation

### For First-Time Users
1. Start with [README.md](../README.md) for quick setup
2. Read [CONFIGURATION.md](CONFIGURATION.md) to set up config.yaml
3. Run `uv run rss-feed-summary --config config.yaml --dry-run once` to test

### For Understanding the System
1. Read [ARCHITECTURE.md](ARCHITECTURE.md) for system overview and diagrams
2. Read [DATAFLOW.md](DATAFLOW.md) to see data flow through the application
3. Review [MODULES.md](MODULES.md) for details on each code module

### For Configuration
- [CONFIGURATION.md](CONFIGURATION.md) - Comprehensive config guide
  - YAML structure
  - All options explained
  - Gmail setup instructions
  - Troubleshooting

### For Development
- [CONTRIBUTING.md](CONTRIBUTING.md) - Development guide
  - Project structure
  - Code style conventions
  - How to add features
  - Common customizations

---

## Document Overview

### ARCHITECTURE.md
**Purpose:** Understand the system design and component relationships

**Contents:**
- High-level architecture diagram (ASCII)
- Core modules overview
- Data flow through the pipeline
- Design patterns used
- Extension points for customization
- Dependency list
- Performance considerations
- Error handling approach
- Security notes

**Read if:** You want to understand how the system works at a high level

---

### MODULES.md
**Purpose:** Detailed reference for each code module and function

**Contents:**
- `config.py` - Configuration loading
- `fetch.py` - RSS feed fetching and thumbnail extraction
- `summarize.py` - Text summarization algorithms
- `emailer.py` - Email rendering and sending
- `health.py` - Feed health checking
- `scheduler.py` - Task scheduling
- `cli.py` - Command orchestration
- `main.py` - CLI entry point

For each module:
- Function signatures with parameters
- Return values
- Algorithm descriptions
- Usage examples

**Read if:** You're working with specific code modules or need API reference

---

### DATAFLOW.md
**Purpose:** Visualize how data moves through the application

**Contents:**
- Complete flow diagram (ASCII) for entire pipeline
- Command-specific flows (once, schedule, check, clean)
- Data structure definitions at each stage
- Error handling flow
- Memory usage patterns
- Performance characteristics

**Read if:** You want to understand data transformation and command execution

---

### CONFIGURATION.md
**Purpose:** Learn how to configure the application for your needs

**Contents:**
- YAML structure and syntax
- Complete reference for all config options
- Real-world examples
- Environment variables
- Secrets management best practices
- Provider-specific setup (Gmail, Outlook, etc.)
- Troubleshooting common errors
- Common configuration patterns

**Read if:** You're setting up config.yaml or having issues with configuration

---

### CONTRIBUTING.md
**Purpose:** Guide for development and customization

**Contents:**
- Project structure and organization
- Development environment setup
- Code style conventions
- Testing approaches
- How to add new features
- Common customizations (Slack, database, etc.)
- Performance optimization tips
- Debugging techniques
- Release checklist

**Read if:** You want to modify the code or extend functionality

---

## Command Reference

### Setup
```bash
cd rss_feed_summary
uv venv
uv pip install -e .
```

### Run Once
```bash
uv run rss-feed-summary --config config.yaml once
```

### Dry Run (preview email)
```bash
uv run rss-feed-summary --config config.yaml --dry-run once
```

### With Date in Subject
```bash
uv run rss-feed-summary --config config.yaml --subject-date once
```

### With Plain-Text Alternative
```bash
uv run rss-feed-summary --config config.yaml --plain-text once
```

### Daily Scheduler
```bash
uv run rss-feed-summary --config config.yaml schedule
```

### Check Feed Health
```bash
uv run rss-feed-summary --config config.yaml check
```

### Clean Dead Feeds
```bash
uv run rss-feed-summary --config config.yaml clean
uv run rss-feed-summary --config config.yaml clean --force
```

---

## Glossary

| Term | Meaning |
|------|---------|
| **RSS** | Really Simple Syndication - feed format |
| **Atom** | Alternative feed format (also supported) |
| **Feedparser** | Python library for parsing RSS/Atom |
| **SMTP** | Simple Mail Transfer Protocol (email sending) |
| **TLS** | Transport Layer Security (encryption) |
| **Jinja2** | Python templating engine |
| **BeautifulSoup** | Python HTML/XML parsing library |
| **Extractive Summary** | Summary made from original sentences (vs. abstractive/generated) |
| **launchd** | macOS service manager (like systemd on Linux) |
| **Entry** | Single article/post from an RSS feed |
| **Feed** | RSS feed source (collection of entries) |

---

## Architecture Overview

```
User Input
    ↓
config.yaml
    ↓
fetch.py (Get feeds)
    ↓
summarize.py (Summarize content)
    ↓
emailer.py (Render email)
    ↓
SMTP Send
    ↓
Recipient inbox
```

---

## Typical Usage Scenarios

### Scenario 1: Get Daily Tech News
1. Add tech news feeds to config.yaml
2. Set schedule time in config
3. Use macOS launchd to run daily
4. Receive HTML email with summaries and thumbnails

### Scenario 2: Team News Digest
1. Configure multiple recipient emails
2. Use corporate SMTP server
3. Add internal blogs and news sources to feeds
4. Schedule for 9 AM daily

### Scenario 3: Academic Papers
1. Use arXiv RSS feeds
2. Increase max_sentences to 5 (more detail needed)
3. Increase max_per_feed to 20 (recent papers)
4. Filter for specific research areas

### Scenario 4: Clean Up Dead Feeds
1. Run `check` command to identify dead feeds
2. Run `clean` command to remove them
3. Save cleaned config.yaml

---

## Troubleshooting Guide

### Email not sending
- Check SMTP credentials in config.yaml
- Use `--dry-run` to verify email generation works
- Check firewall allows outbound SMTP port
- Verify SMTP server settings

### Feeds not updating
- Run `check` command to see feed health
- Check if feed URLs are still active
- Verify internet connection
- Check for rate limiting (some feeds limit requests)

### Summaries too short/long
- Adjust `max_sentences` in config.yaml (default: 3)
- Adjust `max_per_feed` for article count

### Config not loading
- Validate YAML at https://www.yamllint.com/
- Check indentation (spaces, not tabs)
- Ensure required fields present

### Scheduler not running
- Run manually first: `uv run rss-feed-summary ... once`
- Check launchd status: `launchctl list com.example.rss-summary`
- Check logs: `/Users/YOUR_USER/Library/Logs/rss-summary.out`

---

## FAQ

**Q: Can I fetch feeds without sending email?**  
A: Yes, use `--dry-run` flag to preview the email.

**Q: Can I customize the email appearance?**  
A: Yes, edit `templates/email.html.j2` Jinja2 template.

**Q: Can I send to Slack instead of email?**  
A: Not built-in, but see CONTRIBUTING.md for how to add it.

**Q: How do I keep secrets out of git?**  
A: Use `.gitignore` to exclude config files and keep credentials separate.

**Q: Can I run multiple instances with different schedules?**  
A: Yes, use multiple config files and separate commands.

**Q: Is there a database for storing articles?**  
A: No, but you can add one (see CONTRIBUTING.md customization examples).

---

## Getting Help

1. Check relevant documentation files above
2. Search MODULES.md for specific function details
3. Review DATAFLOW.md to understand execution path
4. See CONTRIBUTING.md for development questions
5. Check CONFIGURATION.md for setup issues

