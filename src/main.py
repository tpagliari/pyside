import asyncio
from typing import List, Optional

# internal modules
from wikiMedia.wsearch import wikipedia_search, WikiResult
from reddit.rsearch import get_all_resources


def output_fmt(wiki: Optional[WikiResult], reddit_links: List[str]) -> str:
    """Format std output results"""
    lines = []
    if wiki:
        lines.append("Let's start with a wiki article:")
        lines.append(f"- {wiki.title}: {wiki.url}\n")

    lines.extend(f"- {link}" for link in reddit_links)
    return "\n".join(lines)


async def search(query: str) -> str:
    """Search wiki and reddit, return formatted results"""
    wiki_task = wikipedia_search(query)
    reddit_task = asyncio.to_thread(get_all_resources, query)

    wiki_result, reddit_links = await asyncio.gather(wiki_task, reddit_task)

    return output_fmt(wiki_result, reddit_links)

async def main():
    query = input("What do you want to learn?\n")
    output = await search(query=query)
    print(output)

if __name__ == "__main__":
    asyncio.run(main())