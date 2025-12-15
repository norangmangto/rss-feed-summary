from typing import List, Dict, Any
import time
import feedparser
from tenacity import retry, stop_after_attempt, wait_exponential


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
def fetch_feed(url: str) -> Dict[str, Any]:
    return feedparser.parse(url)


def collect_entries(feed_urls: List[str], max_per_feed: int = 10) -> List[Dict[str, Any]]:
    entries: List[Dict[str, Any]] = []
    for url in feed_urls:
        parsed = fetch_feed(url)
        for e in parsed.entries[:max_per_feed]:
            entries.append(
                {
                    "title": e.get("title", ""),
                    "link": e.get("link", ""),
                    "published": e.get("published", ""),
                    "summary": e.get("summary", ""),
                    "source": parsed.feed.get("title", url),
                    "timestamp": time.time(),
                }
            )
    return entries