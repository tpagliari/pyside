import requests
import socket
from bs4 import BeautifulSoup
from urllib.parse import urlparse, ParseResult
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Iterable, Set, Optional, Dict, Tuple
    

def check_ping(url: str, timeout: int = 2) -> bool:
    """Check if the server accepts TCP connections.
    Careful: this function doesn't guarantee valid HTTP, only tests TCP handshake.
    """
    try:
        parsed: ParseResult = urlparse(url)
        host: str | None    = parsed.hostname
        port: int = 443 if parsed.scheme == "https" else 80
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False
    

def check_url(url: str, timeout: int = 3) -> bool:
    """Return True if the server responds (good link), False if dead.
    This function won't download the whole page, and closes as soon as headers arrive.
    Assumes status code greater or equal to 400 as error.
    """
    try:
        with requests.head(url, timeout=timeout, allow_redirects=True) as r:
            # Fallback to GET if HEAD not supported
            if r.status_code == 405:
                with requests.get(url, stream=True, timeout=timeout) as r2:
                    return r2.status_code < 400
            return r.status_code < 400
    except requests.RequestException:
        return False
    

def deadlink(url: str, timeout: int = 3) -> bool:
    """Check if a link is dead or not. If it's a deadlink, this function
    returns True, else False. This function internally performs
    - check on tcp handshake first -> immediately return True if it fails
    - check the url is valid but closes as soon as headers (and first chunk if needed) arrive.
    You can tailor timeout to be sure that it's enough to get first header.
    """
    if not check_ping(url):
        return True
    return not check_url(url, timeout)


def filter_live_urls(urls: Iterable[str], timeout: int = 3, max_workers: int = 10) -> Set[str]:
    """Filter URLs, keeping only live ones. Returns a set of live URLs.
    Pure functional approach: maps urls -> liveness check -> filter.
    Uses parallel execution for performance.
    """
    def is_live(url: str) -> tuple[str, bool]:
        return (url, not deadlink(url, timeout))
    
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