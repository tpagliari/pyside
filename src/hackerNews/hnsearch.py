from typing import Dict, Optional, List
import requests

# internal lib
import const
from lib import filter_live_urls


def get_json(url: str, params: Optional[Dict] = None, timeout: int = 6) -> Optional[Dict]:
    """Small and reusable http helper
    """
    try:
        r = requests.get(url, params=params, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        # debug
        print(f"While extracting json: {e}")
        return None

def search_hn(query: str, hits: int = 50) -> List[str]:
    """
    Search HN stories via Algolia and return the article URLs (the `url` field).
    Only keeps posts that actually link to an external resource.
    """
    js = get_json(
        url = const.ALGOLIA_SEARCH_URL,
        params = {"query": query, "hitsPerPage": hits, "tags": "story"}
    )
    if not js or "hits" not in js:
        return []

    urls = []
    for hit in js["hits"]:
        url = hit.get("url")
        if url and url.startswith("http"):
            urls.append(url)
    return urls

def get_resources(query: str, hits: int = 50, max_workers: int = 10, timeout: int = 4) -> List[str]:
    """Entry point for HN search:
      - search HN for relevant results
      - collect their external urls
      - filter live links in parallel

    TODO: semanitc scoring when sorting
    """
    urls: List[str] = search_hn(query, hits)
    if not urls:
        return []

    live = filter_live_urls(urls, timeout=timeout, max_workers=max_workers)
    return sorted(live) # see todo


if __name__ == "__main__":
    q = input("Search Hacker News for: ")
    resources = get_resources(q, hits=40)
    print("\nFound resources:\n")
    for u in resources:
        print(u)