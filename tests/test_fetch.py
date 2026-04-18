import pytest
from unittest.mock import patch, MagicMock
from rss_feed_summary.fetch import extract_thumbnail, deduplicate_entries, collect_entries


# --- extract_thumbnail ---

def test_extract_thumbnail_media_thumbnail():
    entry = {"media_thumbnail": [{"url": "https://example.com/thumb.jpg"}]}
    assert extract_thumbnail(entry) == "https://example.com/thumb.jpg"


def test_extract_thumbnail_media_content_image():
    entry = {"media_content": [{"type": "image/jpeg", "url": "https://example.com/img.jpg"}]}
    assert extract_thumbnail(entry) == "https://example.com/img.jpg"


def test_extract_thumbnail_enclosure():
    entry = {"enclosures": [{"type": "image/png", "href": "https://example.com/enc.png"}]}
    assert extract_thumbnail(entry) == "https://example.com/enc.png"


def test_extract_thumbnail_links():
    entry = {
        "links": [{"rel": "enclosure", "type": "image/gif", "href": "https://example.com/link.gif"}]
    }
    assert extract_thumbnail(entry) == "https://example.com/link.gif"


def test_extract_thumbnail_none():
    assert extract_thumbnail({}) == ""


def test_extract_thumbnail_prefers_media_thumbnail_over_others():
    entry = {
        "media_thumbnail": [{"url": "https://example.com/thumb.jpg"}],
        "enclosures": [{"type": "image/png", "href": "https://example.com/enc.png"}],
    }
    assert extract_thumbnail(entry) == "https://example.com/thumb.jpg"


# --- deduplicate_entries ---

def test_deduplicate_entries_removes_exact_link_duplicates():
    entries = [
        {"link": "https://example.com/a", "title": "Article A"},
        {"link": "https://example.com/a", "title": "Article A copy"},
    ]
    result = deduplicate_entries(entries)
    assert len(result) == 1
    assert result[0]["title"] == "Article A"


def test_deduplicate_entries_removes_same_title():
    entries = [
        {"link": "https://example.com/a", "title": "Same Title"},
        {"link": "https://example.com/b", "title": "Same Title"},
    ]
    result = deduplicate_entries(entries)
    assert len(result) == 1


def test_deduplicate_entries_keeps_different_articles():
    entries = [
        {"link": "https://example.com/a", "title": "Article A"},
        {"link": "https://example.com/b", "title": "Article B"},
    ]
    result = deduplicate_entries(entries)
    assert len(result) == 2


def test_deduplicate_entries_keeps_first_occurrence():
    entries = [
        {"link": "https://example.com/a", "title": "First"},
        {"link": "https://example.com/a", "title": "Second"},
    ]
    result = deduplicate_entries(entries)
    assert result[0]["title"] == "First"


def test_deduplicate_entries_empty():
    assert deduplicate_entries([]) == []


def test_deduplicate_entries_no_link_or_title():
    entries = [{"content": "x"}, {"content": "y"}]
    result = deduplicate_entries(entries)
    assert len(result) == 2


# --- collect_entries ---

def _make_mock_feed(title="Feed Title", entries=None):
    mock_feed = MagicMock()
    mock_feed.feed.get.return_value = title
    mock_feed.entries = entries or []
    return mock_feed


def test_collect_entries_uses_content_field():
    entry = MagicMock()
    entry.get.side_effect = lambda k, d="": {"title": "T", "link": "https://x.com", "published": ""}.get(k, d)
    entry.__contains__ = lambda self, k: k == "content"
    entry.__getitem__ = lambda self, k: [{"value": "<p>Full content</p>"}] if k == "content" else []
    entry.content = [{"value": "<p>Full content</p>"}]

    mock_feed = _make_mock_feed(entries=[entry])
    with patch("rss_feed_summary.fetch.fetch_feed", return_value=mock_feed):
        results = collect_entries(["https://example.com/feed"], max_per_feed=1)
    assert results[0]["content"] == "<p>Full content</p>"


def test_collect_entries_respects_max_per_feed():
    entries = [MagicMock() for _ in range(5)]
    for e in entries:
        e.get.return_value = ""
        e.__contains__ = lambda self, k: False
    mock_feed = _make_mock_feed(entries=entries)
    with patch("rss_feed_summary.fetch.fetch_feed", return_value=mock_feed):
        results = collect_entries(["https://example.com/feed"], max_per_feed=3)
    assert len(results) == 3
