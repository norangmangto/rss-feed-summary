from typing import List, Dict, Tuple
import requests
from datetime import datetime


def check_feed_health(feed_urls: List[str], timeout: int = 5) -> List[Dict]:
    """Check health of all feeds and return status for each."""
    results = []
    for url in feed_urls:
        status = check_single_url(url, timeout)
        results.append(status)
    return results


def check_single_url(url: str, timeout: int = 5) -> Dict:
    """Check a single URL and return detailed status."""
    try:
        start = datetime.now()
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        elapsed = (datetime.now() - start).total_seconds()
        
        return {
            "url": url,
            "alive": response.status_code < 400,
            "status_code": response.status_code,
            "response_time_ms": round(elapsed * 1000, 2),
            "error": None,
        }
    except requests.Timeout:
        return {
            "url": url,
            "alive": False,
            "status_code": None,
            "response_time_ms": None,
            "error": f"Timeout after {timeout}s",
        }
    except requests.ConnectionError as e:
        return {
            "url": url,
            "alive": False,
            "status_code": None,
            "response_time_ms": None,
            "error": f"Connection error: {str(e)[:80]}",
        }
    except Exception as e:
        return {
            "url": url,
            "alive": False,
            "status_code": None,
            "response_time_ms": None,
            "error": f"Error: {str(e)[:80]}",
        }


def print_health_report(results: List[Dict]):
    """Pretty-print the health check results."""
    alive_count = sum(1 for r in results if r["alive"])
    total = len(results)
    
    print(f"\n📊 RSS Feed Health Report")
    print(f"═" * 80)
    print(f"Status: {alive_count}/{total} feeds are healthy\n")
    
    for result in results:
        status_icon = "✅" if result["alive"] else "❌"
        status_code = result.get("status_code") or "—"
        response_time = (
            f"{result['response_time_ms']}ms"
            if result["response_time_ms"]
            else "—"
        )
        
        print(f"{status_icon} {result['url']}")
        if result["error"]:
            print(f"   Error: {result['error']}")
        else:
            print(f"   Status: {status_code} | Response time: {response_time}")
    
    print(f"\n{'═' * 80}")


def get_dead_feeds(results: List[Dict]) -> List[str]:
    """Extract URLs of dead feeds from health check results."""
    return [r["url"] for r in results if not r["alive"]]
