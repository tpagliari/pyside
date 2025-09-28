import requests
import socket
from urllib.parse import urlparse, ParseResult


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
    This function won’t download the whole page, and closes as soon as headers arrive.
    """
    try:
        with requests.get(url, stream=True, timeout=timeout) as r:
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