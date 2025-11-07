from typing import Dict, Optional, List
from collections import OrderedDict
from dataclasses import dataclass
import requests

# internal lib
from .const import ALGOLIA_SEARCH_URL
from .lib import filter_live_urls, get_meta_bulk


@dataclass(frozen=True)
class HackerNewsResource:
    title : str
    url : str
    description: Optional[str]

    def __eq__(self, other):
        return self.url == other.url
    
    def __hash__(self):
        return hash(self.url)


def get_json(url: str, params: Optional[Dict] = None, timeout: int = 6) -> Optional[Dict]:
    """Small and reusable http helper for single requests.
    """
    try:
        r = requests.get(url, params=params, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        # debug
        print(f"While extracting json: {e}")
        return None


def search_hn(query: str, hits: int = 50) -> List[HackerNewsResource]:
    """
    Search HN stories via Algolia and return structured results:
    - title
    - external url
    - short description (from story_text or comment_text)

    NOTE: So if you search "machine learning," Algolia returns stories where "machine learning"
    appears in the title/text, with recent popular ones first.
    """
    js = get_json(
        url = ALGOLIA_SEARCH_URL,
        params = {"query": query, "hitsPerPage": hits, "tags": "story"}
    )
    if not js or "hits" not in js:
        return []

    resources : List[HackerNewsResource] = []
    for hit in js["hits"]:
        url   = hit.get("url")
        title = hit.get("title")
        if url and url.startswith("http"):
            resources.append(
                HackerNewsResource(title=title, url=url, description = None)
            )
    return resources


def get_resources(query: str, hits: int = 50, max_workers: int = 30, timeout: int = 3, include_meta: bool = False) -> List[HackerNewsResource]:
    """
    Entry point for HN search:
      - search HN for relevant results
      - filter live links in parallel

    If `include_meta` is True, also a description of the link is fetched:
    with my (not so powerful) machine, with 50 hits, this will cost around
    2-3 seconds more (on 5 seconds) then the same fetch without meta fetch. I would
    say that computational time increases by 50% more or less.

    TODO: semanitc scoring when extracting posts.
    """
    learn_query = f"Learn {query}"
    resources: List[HackerNewsResource] = search_hn(learn_query, hits)
    if (n := len(resources)) < hits:
        resources.extend(search_hn(query, hits-n)) # these articles should be more specialized

    if not resources:
        return []

    live_urls = filter_live_urls([r.url for r in resources], timeout=timeout, max_workers=max_workers)
    live_resources = [r for r in resources if r.url in live_urls]
    live_resources = list(OrderedDict.fromkeys(live_resources))

    if include_meta:
        meta = get_meta_bulk([r.url for r in live_resources])
    else:
        meta = {}

    enriched = [
        HackerNewsResource(
            title = r.title, url = r.url,
            description = meta.get(r.url) if include_meta else None
        ) for r in live_resources
    ]
    return enriched



if __name__ == "__main__":
    q = input("Search Hacker News for: ")
    resources = get_resources(q, hits=40, max_workers=10)
    print("\nFound resources:\n")
    for r in resources:
        print(f"{r.title}\n{r.url}\n{r.description or '(no description)'}\n")