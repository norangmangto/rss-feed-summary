import pytest
from unittest.mock import patch, MagicMock
import requests
from rss_feed_summary.health import check_single_url, check_feed_health, get_dead_feeds


def _mock_response(status_code=200):
    mock = MagicMock()
    mock.status_code = status_code
    return mock


# --- check_single_url ---

def test_check_single_url_alive():
    with patch("rss_feed_summary.health.requests.head", return_value=_mock_response(200)):
        result = check_single_url("https://example.com/feed")
    assert result["alive"] is True
    assert result["status_code"] == 200
    assert result["error"] is None


def test_check_single_url_404_is_dead():
    with patch("rss_feed_summary.health.requests.head", return_value=_mock_response(404)):
        result = check_single_url("https://example.com/gone")
    assert result["alive"] is False
    assert result["status_code"] == 404


def test_check_single_url_timeout():
    with patch("rss_feed_summary.health.requests.head", side_effect=requests.Timeout):
        result = check_single_url("https://example.com/feed", timeout=1)
    assert result["alive"] is False
    assert result["status_code"] is None
    assert "Timeout" in result["error"]


def test_check_single_url_connection_error():
    with patch("rss_feed_summary.health.requests.head", side_effect=requests.ConnectionError("refused")):
        result = check_single_url("https://example.com/feed")
    assert result["alive"] is False
    assert "Connection error" in result["error"]


def test_check_single_url_unexpected_error():
    with patch("rss_feed_summary.health.requests.head", side_effect=RuntimeError("boom")):
        result = check_single_url("https://example.com/feed")
    assert result["alive"] is False
    assert "boom" in result["error"]


def test_check_single_url_includes_response_time():
    with patch("rss_feed_summary.health.requests.head", return_value=_mock_response(200)):
        result = check_single_url("https://example.com/feed")
    assert result["response_time_ms"] is not None
    assert result["response_time_ms"] >= 0


# --- check_feed_health ---

def test_check_feed_health_returns_one_result_per_url():
    urls = ["https://a.com/feed", "https://b.com/feed"]
    with patch("rss_feed_summary.health.requests.head", return_value=_mock_response(200)):
        results = check_feed_health(urls)
    assert len(results) == 2
    assert {r["url"] for r in results} == set(urls)


def test_check_feed_health_empty():
    assert check_feed_health([]) == []


# --- get_dead_feeds ---

def test_get_dead_feeds_returns_only_dead():
    results = [
        {"url": "https://alive.com", "alive": True},
        {"url": "https://dead.com", "alive": False},
        {"url": "https://also-dead.com", "alive": False},
    ]
    dead = get_dead_feeds(results)
    assert dead == ["https://dead.com", "https://also-dead.com"]


def test_get_dead_feeds_all_alive():
    results = [{"url": "https://alive.com", "alive": True}]
    assert get_dead_feeds(results) == []


def test_get_dead_feeds_empty():
    assert get_dead_feeds([]) == []
