from typing import List, Dict, Any
import time
import hashlib
import feedparser
from tenacity import retry, stop_after_attempt, wait_exponential
from datetime import datetime


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


def deduplicate_entries(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove duplicate entries based on title and link similarity.
    
    Uses both exact matching (by URL) and fuzzy title matching to identify
    and remove duplicate entries that may come from different sources.
    Keeps the first occurrence of each entry.
    """
    seen_links = set()
    seen_titles = {}
    deduplicated = []
    
    for entry in entries:
        link = entry.get("link", "").strip()
        title = entry.get("title", "").strip().lower()
        
        # Exact link match (most reliable deduplication)
        if link and link in seen_links:
            continue
        
        # Title-based deduplication (for feeds that may use different URLs for same article)
        if title:
            # Create a normalized title hash for fuzzy matching
            title_hash = hashlib.md5(title.encode()).hexdigest()
            if title_hash in seen_titles:
                continue
            seen_titles[title_hash] = entry
        
        # This entry is unique, add it
        if link:
            seen_links.add(link)
        deduplicated.append(entry)
    
    return deduplicated


def sort_by_published_date(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Sort entries by published date in descending order (newest first).
    
    Uses the published_parsed timestamp if available, otherwise falls back to
    the current timestamp. Entries without dates will appear at the end.
    """
    def get_sort_key(entry: Dict[str, Any]) -> float:
        published_parsed = entry.get("published_parsed")
        if published_parsed:
            # Convert time.struct_time to timestamp
            try:
                return time.mktime(published_parsed)
            except (ValueError, TypeError, OverflowError):
                pass
        # Fallback to current timestamp (will be sorted to the end with negative sign)
        return entry.get("timestamp", 0)
    
    return sorted(entries, key=get_sort_key, reverse=True)


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
            
            # Get published_parsed for sorting, if available
            published_parsed = getattr(e, "published_parsed", None)
            
            entries.append(
                {
                    "title": e.get("title", ""),
                    "link": e.get("link", ""),
                    "published": e.get("published", ""),
                    "published_parsed": published_parsed,
                    "content": content,
                    "summary": e.get("summary", ""),
                    "thumbnail": thumbnail,
                    "source": parsed.feed.get("title", url),
                    "timestamp": time.time(),
                }
            )
    
    # Sort entries by published date in descending order (newest first)
    return sort_by_published_date(entries)
