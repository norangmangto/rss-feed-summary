import sqlite3
import os
from typing import List, Dict, Any

DEFAULT_DB_PATH = os.path.expanduser("~/.cache/rss-feed-summary/seen.db")


def init_db(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS seen_items (
            link TEXT PRIMARY KEY,
            title TEXT,
            source TEXT,
            fetched_at REAL
        )
        """
    )
    conn.commit()
    return conn


def filter_new_items(
    conn: sqlite3.Connection, items: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Return only items whose link has not been seen before."""
    new_items = []
    for item in items:
        link = item.get("link", "").strip()
        if not link:
            new_items.append(item)
            continue
        row = conn.execute(
            "SELECT 1 FROM seen_items WHERE link = ?", (link,)
        ).fetchone()
        if row is None:
            new_items.append(item)
    return new_items


def mark_seen(conn: sqlite3.Connection, items: List[Dict[str, Any]]) -> None:
    """Persist items to the seen cache."""
    rows = [
        (
            item.get("link", "").strip(),
            item.get("title", ""),
            item.get("source", ""),
            item.get("timestamp", 0.0),
        )
        for item in items
        if item.get("link", "").strip()
    ]
    conn.executemany(
        "INSERT OR IGNORE INTO seen_items (link, title, source, fetched_at) VALUES (?, ?, ?, ?)",
        rows,
    )
    conn.commit()
