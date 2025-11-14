import asyncio

# internal modules
from .wikiMedia.wsearch import wikipedia_search
from .reddit.rsearch import get_all_resources as reddit_search
from .hackerNews.hnsearch import get_resources as hn_search
from .arXiv.asearch import get_resources as arxiv_search


async def stream_arxiv(query: str, n: int):
    loop = asyncio.get_running_loop()
    gen = await loop.run_in_executor(None, lambda: arxiv_search(query, n))

    for item in gen:
        yield item


async def search_stream(query: str):
    """Async generator yielding partial results as they arrive.
    """
    
    wiki_task = asyncio.create_task(
        wikipedia_search(query))
    
    reddit_task = asyncio.create_task(
        asyncio.to_thread(reddit_search, query, 2, 2))
    
    hn_task = asyncio.create_task(
        asyncio.to_thread(hn_search, query, hits=10, include_meta=True))
    
    arxiv_gen = stream_arxiv(query, 5)
    arxiv_task = asyncio.create_task(arxiv_gen.__anext__())

    tasks = {
        "wiki": wiki_task,
        "reddit": reddit_task,
        "hn": hn_task,
        "arxiv": arxiv_task
    }

    pending = set(tasks.values())
    while pending:
        done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
        for d in done:

            if d == tasks["wiki"]:
                wiki = d.result()
                yield ("WikiMedia", [f"{wiki.title}\n  {wiki.url}\n (No description)"])
            elif d == tasks["hn"]:
                hn_resources = d.result()
                lines = [
                    f"{r.title}\n  {r.url}\n  {r.description or '(No description)'}" for r in hn_resources
                ]
                yield ("HackerNews", lines)

            elif d == tasks["reddit"]:
                reddit_links = d.result()
                yield ("Reddit", [f"(No title)\n {link}\n (No description)" for link in reddit_links])

            elif d == tasks["arxiv"]:
                try:
                    r = d.result()
                    yield ("arXiv", [f"{r.title}\n  {r.url}\n  {r.description}"])
                    # schedule next arxiv result
                    tasks["arxiv"] = asyncio.create_task(arxiv_gen.__anext__())
                    pending.add(tasks["arxiv"])
                except StopAsyncIteration:
                    # no more arxiv results
                    pass


async def main():
    """Only for CLI usage"""
    q = input("What would you like to learn?\n")
    async for src, lines in search_stream(q):
        print(f"{src}: {lines}")


if __name__ == "__main__":
    asyncio.run(main())