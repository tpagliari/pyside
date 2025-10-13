from typing import Optional, List, Any, Tuple
from dataclasses import dataclass
import aiohttp
from functools import reduce


@dataclass(frozen=True)
class WikiResult:
    title: str
    url: str


API_BASE = "https://en.wikipedia.org/w/api.php"


def search_params(term: str) -> dict:
    return {
        "action": "query",
        "format": "json",
        "list": "search",
        "formatversion": "2",
        "srlimit": "1",
        "srsearch": term,
    }


def get_at(path: List[str], obj: dict) -> Optional[Any]:
    """Navigate nested dict by path."""
    return reduce(
        lambda acc, key: acc.get(key) if isinstance(acc, dict) else None,
        path,
        obj
    )


def get_array_at(path: List[str], idx: int, obj: dict) -> Optional[Any]:
    """Get array element at path and index."""
    val = get_at(path, obj)
    return val[idx] if isinstance(val, List) and 0 <= idx < len(val) else None


def get_page_info(obj: dict) -> Optional[Tuple]:
    """Extract page info from search response."""
    page = get_array_at(["query", "search"], 0, obj)
    return (page["pageid"], page["title"]) if page and "pageid" in page else None


def get_suggestion(obj: dict) -> Optional[str]:
    """Extract search suggestion."""
    return get_at(["query", "searchinfo", "suggestion"], obj)


def mk_url(pageid: int) -> str:
    """Create Wikipedia URL from page ID."""
    return f"https://en.wikipedia.org/?curid={pageid}"


async def call_api(params: dict) -> dict:
    """Make API call with given params."""
    headers = {"User-Agent": "WikipediaSearch/1.0"}
    async with aiohttp.ClientSession() as session:
        async with session.get(API_BASE, params=params, headers=headers) as response:
            return await response.json()


async def wikipedia_search(search_term: str) -> Optional[WikiResult]:
    """Search Wikipedia and return result."""
    obj = await call_api(search_params(search_term))
    
    page_info = get_page_info(obj)
    if page_info:
        pageid, title = page_info

        return WikiResult(title, mk_url(pageid))
    
    # Try suggestion:
    # usually, it's used when the user insert a typo in the search term
    # and the wikipedia API provide a suggested search term
    suggestion = get_suggestion(obj)
    if not suggestion:
        return None
    
    obj = await call_api(search_params(suggestion))
    page_info = get_page_info(obj)
    if page_info:
        pageid, title = page_info

        return WikiResult(title, mk_url(pageid))
    
    return None



if __name__ == "__main__":
    import asyncio

    input : str = input("What do you want to learn?\n")

    async def main():
        result = await wikipedia_search(input)
        if result:
            print(f"Title: {result.title}")
            print(f"URL: {result.url}")
    
    asyncio.run(main())