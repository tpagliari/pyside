import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Iterable, Set, Optional, Dict, Tuple
    

def check_url(url: str, timeout: int = 3) -> bool:
    """
    Return True if URL responds with <400 status.
    In this case we assume the link is not dead.
    """
    try:
        with requests.get(url, stream=True, timeout=timeout, allow_redirects=True) as r:
            return r.status_code < 400
    except requests.RequestException:
        return False


def filter_live_urls(urls: Iterable[str], timeout: int = 3, max_workers: int = 10) -> Set[str]:
    """Filter URLs, keeping only live ones. Returns a set of live URLs.
    Pure functional approach: maps urls -> liveness check -> filter.
    Uses parallel execution for performance.
    """
    def is_live(url: str) -> tuple[str, bool]:
        return (url, check_url(url, timeout))
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(is_live, url): url for url in urls}
        return {url for future in as_completed(futures) 
                if (result := future.result()) and result[1]
                for url in [result[0]]}
    

def get_meta(url: str, timeout: int = 3) -> Optional[str]:
    """Try to extract a short meta description from the target page."""
    try:
        r = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        desc = soup.find("meta", attrs={"name": "description"})
        if desc and desc.get("content"):
            return str(desc["content"]).strip()

        # fallback: use first paragraph
        p = soup.find("p")
        if p:
            text = " ".join(p.get_text().strip().split()[:50])
            return text

        return None
    except requests.RequestException:
        return None
    

def get_meta_bulk(urls: Iterable[str], timeout: int = 3, max_workers : int = 10) -> Dict[str, Optional[str]]:
    """
    Fetch meta descriptions for multiple URLs in parallel.
    Returns {url: description or None}.
    """

    def fetch(u: str) -> Tuple[str, Optional[str]]:
        return (u, get_meta(u, timeout))
    
    results : Dict[str, Optional[str]] = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(fetch, url): url for url in urls}
        for future in as_completed(futures):
            url, desc = future.result()
            results[url] = desc
            
    return results