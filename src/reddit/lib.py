import requests
import socket
from urllib.parse import urlparse, ParseResult
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Iterable, Set
    

def check_ping(url: str, timeout: int = 1) -> bool:
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
    

def http_alive(url: str, timeout: int = 2) -> bool:
    """Lightweight HTTP check — HEAD first, fallback to GET if needed."""
    try:
        with requests.head(url, timeout=timeout, allow_redirects=True) as r:
            if r.status_code == 405:
                # case: head not supported
                with requests.get(url, stream=True, timeout=timeout) as r2:
                    return r2.status_code < 400
            return r.status_code < 400
    except requests.RequestException:
        return False


def islive(url: str, tcp_timeout=1, http_timeout=2) -> bool:
    """Check if a link is live (returns True) or not (returns False)"""
    if not check_ping(url, tcp_timeout):
        return False
    return http_alive(url, http_timeout)


def filter_live_urls(urls: Iterable[str], max_workers: int = 10) -> Set[str]:
    """
    Filter URLs, keeping only live ones. Returns a set of live URLs.
    Uses parallel execution for performance.
    
    TODO: make timeout a parameter
    """
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(islive, url): url for url in urls}
        return {futures[f] for f in as_completed(futures) if f.result()}