from typing import Optional
from .config import load_config
from .fetch import collect_entries, deduplicate_entries
from .summarize import summarize_items
from .emailer import render_email, render_text, send_email
from .health import check_feed_health, print_health_report, get_dead_feeds
from .scheduler import run_daily
from .cache import DEFAULT_DB_PATH, init_db, filter_new_items, mark_seen
from datetime import date
import yaml


def check_feeds(config_path: Optional[str] = None):
    cfg = load_config(config_path)
    feeds = cfg["feeds"]
    results = check_feed_health(feeds)
    print_health_report(results)


def clean_feeds(config_path: Optional[str] = None, force: bool = False):
    """Remove dead feeds from config and save."""
    from .config import DEFAULT_CONFIG_PATH
    
    cfg_path = config_path or DEFAULT_CONFIG_PATH
    cfg = load_config(cfg_path)
    feeds = cfg["feeds"]
    
    print(f"\n🔍 Checking {len(feeds)} feeds...")
    results = check_feed_health(feeds)
    dead_urls = get_dead_feeds(results)
    
    if not dead_urls:
        print("✅ All feeds are healthy! No cleanup needed.")
        return
    
    print(f"\n⚠️  Found {len(dead_urls)} dead feed(s):")
    for url in dead_urls:
        print(f"  - {url}")
    
    if not force:
        response = input(f"\nRemove {len(dead_urls)} dead feed(s) from {cfg_path}? (y/n) ")
        if response.lower() != 'y':
            print("Cancelled.")
            return
    
    # Filter out dead feeds
    original_count = len(cfg["feeds"])
    cfg["feeds"] = [url for url in cfg["feeds"] if url not in dead_urls]
    new_count = len(cfg["feeds"])
    
    # Write back to config
    with open(cfg_path, 'w', encoding='utf-8') as f:
        yaml.dump(cfg, f, default_flow_style=False, sort_keys=False)
    
    print(f"\n✅ Updated {cfg_path}")
    print(f"   Removed {original_count - new_count} feed(s)")
    print(f"   Active feeds: {new_count}")


def run_once(
    config_path: Optional[str] = None,
    dry_run: bool = False,
    subject_date: bool = False,
    plain_text: bool = False,
):
    cfg = load_config(config_path)
    feeds = cfg["feeds"]
    limits = cfg.get("limits", {})
    max_per_feed = int(limits.get("max_per_feed", 10))
    max_sentences = int(limits.get("max_sentences", 3))
    db_path = cfg.get("cache", {}).get("db_path", DEFAULT_DB_PATH)

    items = collect_entries(feeds, max_per_feed=max_per_feed)
    items = deduplicate_entries(items)

    conn = init_db(db_path)
    new_items = filter_new_items(conn, items)

    if not new_items:
        print("No new items since last run.")
        conn.close()
        return

    mark_seen(conn, new_items)
    conn.close()

    summarized = summarize_items(new_items, max_sentences=max_sentences)

    email_cfg = cfg["email"]
    subject = email_cfg.get("subject", "Daily RSS Summary")
    if subject_date:
        subject = f"{subject} — {date.today().isoformat()}"
    html = render_email(summarized, subject)
    text = render_text(summarized, subject) if plain_text else None

    if dry_run:
        print(html)
        return
    else:
        send_email(
            html_body=html,
            smtp_host=email_cfg["smtp_host"],
            smtp_port=int(email_cfg.get("smtp_port", 587)),
            username=email_cfg.get("username"),
            password=email_cfg.get("password"),
            mail_from=email_cfg["from"],
            mail_to=email_cfg["to"] if isinstance(email_cfg["to"], list) else [email_cfg["to"]],
            subject=subject,
            use_tls=bool(email_cfg.get("use_tls", True)),
            text_body=text,
        )


def run_scheduler(config_path: Optional[str] = None):
    cfg = load_config(config_path)
    sched = cfg.get("schedule", {})
    hour = int(sched.get("hour", 8))
    minute = int(sched.get("minute", 0))

    def job():
        run_once(config_path, dry_run=False)

    run_daily(hour, minute, job)