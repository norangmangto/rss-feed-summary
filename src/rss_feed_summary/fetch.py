from typing import List, Dict, Any
import time
import feedparser
from tenacity import retry, stop_after_attempt, wait_exponential


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
def fetch_feed(url: str) -> Dict[str, Any]:
    return feedparser.parse(url)


def extract_thumbnail(entry: Dict[str, Any]) -> str:
    """Extract thumbnail/image URL from various RSS fields."""
    # Try media:thumbnail
    if "media_thumbnail" in entry and entry["media_thumbnail"]:
        return entry["media_thumbnail"][0].get("url", "")
    
    # Try media:content
    if "media_content" in entry and entry["media_content"]:
        for media in entry["media_content"]:
            if media.get("medium") == "image" or media.get("type", "").startswith("image/"):
                return media.get("url", "")
    
    # Try enclosures
    if "enclosures" in entry and entry["enclosures"]:
        for enc in entry["enclosures"]:
            if enc.get("type", "").startswith("image/"):
                return enc.get("href", "")
    
    # Try links with image rel
    if "links" in entry:
        for link in entry["links"]:
            if link.get("rel") == "enclosure" and link.get("type", "").startswith("image/"):
                return link.get("href", "")
    
    return ""


def collect_entries(feed_urls: List[str], max_per_feed: int = 10) -> List[Dict[str, Any]]:
    entries: List[Dict[str, Any]] = []
    for url in feed_urls:
        parsed = fetch_feed(url)
        for e in parsed.entries[:max_per_feed]:
            # Get full content if available, otherwise use summary
            content = ""
            if "content" in e and e["content"]:
                content = e["content"][0].get("value", "")
            elif "summary_detail" in e:
                content = e["summary_detail"].get("value", "")
            elif "summary" in e:
                content = e.get("summary", "")
            
            thumbnail = extract_thumbnail(e)
            
            entries.append(
                {
                    "title": e.get("title", ""),
                    "link": e.get("link", ""),
                    "published": e.get("published", ""),
                    "content": content,
                    "summary": e.get("summary", ""),
                    "thumbnail": thumbnail,
                    "source": parsed.feed.get("title", url),
                    "timestamp": time.time(),
                }
            )
    return entries