import asyncio
from typing import List, Optional, Callable

# internal modules
from wikiMedia.wsearch import wikipedia_search, WikiResult
import reddit.rsearch as reddit
import hackerNews.hnsearch as hn


def output_fmt(wiki: Optional[WikiResult] = None,
               reddit_links: List[str]    = [],
               hn_links: List[str]        = []) -> str:
    """Format std output results"""
    lines = []
    if wiki:
        lines.append(f"- {wiki.title}: {wiki.url}")

    lines.extend(f"- {link}" for link in reddit_links)
    lines.extend(f"- {link}" for link in hn_links)
    return "\n".join(lines)


async def search_stream(query: str):
    """Async generator yielding partial results as they arrive.
    """
    
    wiki_task = asyncio.create_task(
        wikipedia_search(query))
    
    reddit_task = asyncio.create_task(
        asyncio.to_thread(reddit.get_all_resources, query, 2, 2))
    
    hn_task = asyncio.create_task(
        asyncio.to_thread(hn.get_resources, query, hits=10))

    tasks = {
        "wiki": wiki_task,
        "reddit": reddit_task,
        "hn": hn_task
    }

    pending = set(tasks.values())
    while pending:
        done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
        for d in done:
            if d == tasks["wiki"]:
                wiki = d.result()
                yield ("WikiMedia", [f"- {wiki.title}: {wiki.url}"])
            elif d == tasks["hn"]:
                hn_links = d.result()
                yield ("HackerNews", [f"- {link}" for link in hn_links])
            elif d == tasks["reddit"]:
                reddit_links = d.result()
                yield ("Reddit", [f"- {link}" for link in reddit_links])


async def search(query: str) -> str:
    """Search wiki and reddit, return formatted results"""
    wiki_task = wikipedia_search(query)
    reddit_task = asyncio.to_thread(reddit.get_all_resources, query, 2, 2)
    hn_task = asyncio.to_thread(hn.get_resources, query, hits=10)

    wiki_result, reddit_links, hn_links = await asyncio.gather(
        wiki_task, reddit_task, hn_task
    )

    return output_fmt(wiki_result, reddit_links, hn_links)

async def main():
    query = input("What do you want to learn?\n")
    output = await search(query=query)
    print(output)

if __name__ == "__main__":
    asyncio.run(main())