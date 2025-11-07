import asyncio

# internal modules
from .wikiMedia.wsearch import wikipedia_search
from .reddit.rsearch import get_all_resources as reddit_search
from .hackerNews.hnsearch import get_resources as hn_search


async def search_stream(query: str):
    """Async generator yielding partial results as they arrive.
    """
    
    wiki_task = asyncio.create_task(
        wikipedia_search(query))
    
    reddit_task = asyncio.create_task(
        asyncio.to_thread(reddit_search, query, 2, 2))
    
    hn_task = asyncio.create_task(
        asyncio.to_thread(hn_search, query, hits=10, include_meta=True))

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
                yield ("WikiMedia", [f"- {wiki.title}\n  {wiki.url}"])
            elif d == tasks["hn"]:
                hn_resources = d.result()
                lines = [
                    f"- {r.title}\n  {r.url}\n  {r.description or '(no description)'}" for r in hn_resources
                ]
                yield ("HackerNews", lines)
            elif d == tasks["reddit"]:
                reddit_links = d.result()
                yield ("Reddit", [f"- {link}" for link in reddit_links])


async def main():
    """Only for CLI usage"""
    q = input("What would you like to learn?\n")
    async for src, lines in search_stream(q):
        print(f"{src}: {lines}")


if __name__ == "__main__":
    asyncio.run(main())