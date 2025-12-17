# Configuration Guide

## YAML Structure

The application requires a `config.yaml` file with the following structure:

```yaml
# List of RSS feed URLs to fetch
feeds:
  - https://example.com/feed1
  - https://example.com/feed2
  - https://example.com/feed3

# Optional: Processing limits
limits:
  max_per_feed: 10      # Max articles per feed (default: 10)
  max_sentences: 3      # Max sentences in summary (default: 3)

# Email delivery settings (required)
email:
  # SMTP server configuration
  smtp_host: smtp.gmail.com
  smtp_port: 587
  
  # Authentication
  username: your-email@gmail.com
  password: your-app-password      # Not your Gmail password!
  
  # Addresses
  from: your-email@gmail.com
  to: 
    - recipient1@example.com
    - recipient2@example.com
  
  # Email settings
  subject: "Daily RSS Summary"
  use_tls: true                     # TLS encryption (default: true)

# Daily schedule (for 'schedule' command)
schedule:
  hour: 8                           # Hour (0-23)
  minute: 0                         # Minute (0-59)
```

## Complete Real-World Example

```yaml
feeds:
  # Tech News
  - https://techcrunch.com/feed/
  - https://news.ycombinator.com/rss
  - https://www.theverge.com/rss/index.xml
  
  # AI & Machine Learning
  - https://openai.com/news/rss.xml
  - https://research.googleblog.com/feeds/posts/default
  - https://aws.amazon.com/blogs/machine-learning/feed/
  
  # Personal blogs
  - https://paulgraham.com/index.html
  - https://xkcd.com/rss.xml

limits:
  max_per_feed: 5
  max_sentences: 3

email:
  smtp_host: smtp.gmail.com
  smtp_port: 587
  username: notifications@example.com
  password: xxxx xxxx xxxx xxxx      # Gmail app password (16 chars)
  from: notifications@example.com
  to:
    - john@example.com
    - team@example.com
  subject: "Daily News Digest"
  use_tls: true

schedule:
  hour: 9
  minute: 0
```

## Configuration Options

### feeds (Required)
**Type:** List of strings  
**Required:** Yes  
**Description:** RSS/Atom feed URLs to fetch

**Validation:**
- Must be non-empty list
- Each URL must be a valid HTTP(S) URL

**Example:**
```yaml
feeds:
  - https://example.com/feed.xml
  - https://example.com/rss
```

### limits (Optional)
**Type:** Object  
**Required:** No  
**Default:** `max_per_feed: 10, max_sentences: 3`

#### limits.max_per_feed
**Type:** Integer  
**Default:** 10  
**Description:** Maximum number of articles to fetch per feed

**Considerations:**
- Higher = more content = larger email
- Lower = faster processing
- Typical range: 5-20

#### limits.max_sentences
**Type:** Integer  
**Default:** 3  
**Description:** Maximum sentences in generated summary

**Considerations:**
- 1-2 sentences: Very brief summaries
- 3-4 sentences: Good balance
- 5+ sentences: More detail

### email (Required)

#### email.smtp_host
**Type:** String  
**Required:** Yes  
**Description:** SMTP server address

**Common values:**
```
Gmail:       smtp.gmail.com
Outlook:     smtp-mail.outlook.com
SendGrid:    smtp.sendgrid.net
AWS SES:     email-smtp.{region}.amazonaws.com
Yahoo:       smtp.mail.yahoo.com
Custom:      mail.yourdomain.com
```

#### email.smtp_port
**Type:** Integer  
**Default:** 587  
**Description:** SMTP port number

**Common values:**
```
587   - TLS (most common)
465   - SSL (legacy)
25    - Unencrypted (rarely used)
```

#### email.username
**Type:** String  
**Required:** If server requires auth  
**Description:** SMTP authentication username

**Usually:**
- Full email address: `user@example.com`
- Or: `username` (depends on server)

#### email.password
**Type:** String  
**Required:** If server requires auth  
**Description:** SMTP authentication password

**Security:**
- Keep out of version control (git)
- Use app-specific passwords where available
- Never use main account password with third-party apps

**Examples:**
```
Gmail:
  - Generate app password (not Gmail password)
  - Visit: https://myaccount.google.com/apppasswords
  - Use 16-character password

Outlook:
  - Use Microsoft account password
  - Or: Generate app password if 2FA enabled

SendGrid:
  - Use "apikey" as username
  - API key as password
```

#### email.from
**Type:** String  
**Required:** Yes  
**Description:** From address in email

**Notes:**
- Usually same as `username` for SMTP
- Must be email address
- Recipient servers may reject if mismatch

#### email.to
**Type:** String or List[String]  
**Required:** Yes  
**Description:** Recipient email address(es)

**Examples:**
```yaml
# Single recipient
to: user@example.com

# Multiple recipients
to:
  - user1@example.com
  - user2@example.com
  - user3@example.com
```

#### email.subject
**Type:** String  
**Default:** "Daily RSS Summary"  
**Description:** Email subject line

**Usage with flags:**
- Default: `Daily RSS Summary`
- With `--subject-date`: `Daily RSS Summary — 2025-12-15`

#### email.use_tls
**Type:** Boolean  
**Default:** true  
**Description:** Enable TLS encryption for SMTP

**Notes:**
- Should be `true` for port 587
- Set `false` for port 25 (if unencrypted)
- Strongly recommended: `true`

### schedule (Optional)
**Type:** Object  
**Required:** No  
**Default:** `hour: 8, minute: 0`

#### schedule.hour
**Type:** Integer (0-23)  
**Default:** 8  
**Description:** Hour to run daily job (24-hour format)

#### schedule.minute
**Type:** Integer (0-59)  
**Default:** 0  
**Description:** Minute to run daily job

**Example:**
```yaml
schedule:
  hour: 14      # 2:00 PM
  minute: 30    # 2:30 PM = 14:30
```

---

## Environment Variables

### RSS_SUMMARY_CONFIG
Set default config path without CLI flag:

```bash
export RSS_SUMMARY_CONFIG=/path/to/custom/config.yaml
uv run rss-feed-summary once      # Uses custom config
```

---

## Secrets Management

### Best Practices

1. **Use app-specific passwords** (Gmail, Outlook, etc.)
2. **Keep config.yaml out of git:**
   ```bash
   echo "config.yaml" >> .gitignore
   echo "config.*.yaml" >> .gitignore
   ```

3. **Use environment variables** for secrets:
   ```yaml
   # config.yaml
   email:
     smtp_host: smtp.gmail.com
     username: ${SMTP_USER}      # Not supported yet
     password: ${SMTP_PASS}
   ```

4. **Separate production config:**
   ```bash
   cp config.yaml config.local.yaml
   # Edit config.local.yaml with real credentials
   uv run rss-feed-summary --config config.local.yaml once
   ```

5. **Set file permissions:**
   ```bash
   chmod 600 config.yaml      # Only you can read
   ```

---

## Gmail Setup Guide

### Step 1: Enable 2FA
1. Go to https://myaccount.google.com/security
2. Scroll to "How you sign in to Google"
3. Enable "2-Step Verification"

### Step 2: Create App Password
1. Go to https://myaccount.google.com/apppasswords
2. Select "Mail" and "Windows Computer" (or your device)
3. Click "Generate"
4. Copy the 16-character password

### Step 3: Configure config.yaml
```yaml
email:
  smtp_host: smtp.gmail.com
  smtp_port: 587
  username: your-email@gmail.com
  password: xxxx xxxx xxxx xxxx    # 16-char app password
  from: your-email@gmail.com
  to: recipient@example.com
  use_tls: true
```

### Test Connection
```bash
uv run rss-feed-summary --config config.yaml --dry-run once
```

---

## Common Configuration Patterns

### Minimal Config
```yaml
feeds:
  - https://example.com/feed

email:
  smtp_host: smtp.gmail.com
  username: you@gmail.com
  password: xxxx xxxx xxxx xxxx
  from: you@gmail.com
  to: you@gmail.com
```

### Multiple Recipients
```yaml
email:
  to:
    - team@example.com
    - manager@example.com
    - you@example.com
```

### Large Feed List
```yaml
feeds:
  # News
  - https://news.ycombinator.com/rss
  - https://techcrunch.com/feed/
  
  # Blogs
  - https://blog1.com/feed
  - https://blog2.com/feed
  
  # Professional
  - https://industry-news.com/rss

limits:
  max_per_feed: 3      # Keep emails smaller
  max_sentences: 2
```

### Multiple Daily Summaries
Use multiple config files:
```bash
# Morning summary at 8 AM
uv run rss-feed-summary --config config.morning.yaml schedule

# Evening summary at 6 PM (different shell)
uv run rss-feed-summary --config config.evening.yaml schedule
```

### Niche Feeds Only
```yaml
feeds:
  - https://research.google/pubs/rss/
  - https://papers.ssrn.com/sol3/rss_topics.cfm?topicid=1800000
  - https://arxiv.org/list/cs.AI/rss

limits:
  max_per_feed: 20
  max_sentences: 5      # Academic summaries need more context
```

---

## Troubleshooting Configuration

### Error: "config.yaml must contain a 'feeds' list"
**Cause:** Missing `feeds` section or not a list  
**Fix:** Add valid feeds list to config.yaml

### Error: "email.smtp_host is required"
**Cause:** Missing SMTP server address  
**Fix:** Add `smtp_host:` under `email:` section

### Error: "email.from and email.to are required"
**Cause:** Missing sender or recipient  
**Fix:** Add both addresses

### Error: "SMTP auth failed"
**Cause:** Wrong username/password  
**Fix:** 
- Gmail: Use app password, not Gmail password
- Verify credentials with SMTP provider
- Check if 2FA is required

### Error: "Connection timeout"
**Cause:** SMTP server unreachable  
**Fix:**
- Check smtp_host and smtp_port
- Verify firewall allows outbound port
- Test with `telnet smtp.example.com 587`

### Config not loading
**Cause:** YAML syntax error  
**Fix:**
- Check indentation (use spaces, not tabs)
- Validate at: https://www.yamllint.com/
- Check for special characters needing quotes

