from dataclasses import dataclass
import aiohttp
import asyncio


@dataclass(frozen=True)
class SubReddit:
    def from_json(data):
        this = SubReddit(
            id=data["id"],
            title=data["title"],
            subs=data["subscribers"],
            category=data["advertiser_category"],
            description=data["description"],
            public_description=data["public_description"],
            lang=data["lang"],
        )

        return this

    title: str
    subs: int
    category: str
    public_description: str
    description: str
    id: int
    lang: str


async def fetch_popular_subreddits(total: int, page_size: int):
    subreddits = []

    async with aiohttp.ClientSession() as session:
        url = "https://www.reddit.com/subreddits/popular.json"
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux i686; rv:143.0) Gecko/20100101 Firefox/143.0"
        }

        count = 0
        after = ""

        async with aiohttp.ClientSession() as session:
            while total > count:
                params = {
                    "limit": page_size,
                }

                if count > 0:
                    params["after"] = after

                async with session.get(url, params=params, headers=headers) as response:
                    data = (await response.json())["data"]

                    subreddits_data = map(lambda entry: entry["data"], data["children"])

                    count += data["dist"]
                    after = data["after"]

                    subreddits_chunk = [
                        SubReddit.from_json(entry)
                        for entry in subreddits_data
                        if filter_subreddit(entry)
                    ]
                    process_chunk(subreddits_chunk)
                    subreddits.extend(subreddits_chunk)

        return subreddits


def process_chunk(subreddits):
    print(subreddits[0].title)


def filter_subreddit(obj):
    return (not obj["over18"]) and (obj["subscribers"] > 5000)


async def main():
    data = await fetch_popular_subreddits(total=10, page_size=1)
    print([subreddit.title for subreddit in data])


# ruff format  src/reddit/subreddit-prober.py
if __name__ == "__main__":
    asyncio.run(main())
