from dataclasses import dataclass
from typing import Optional, Iterable
from collections import OrderedDict
import arxiv


@dataclass(frozen=True)
class ArxivResource:
    title: str
    url: str
    description: Optional[str]

    def __eq__(self, other):
        return self.url == other.url
    
    def __hash__(self):
        return hash(self.url)
    

def deduplicate(xs: Iterable) -> Iterable:
    """Ensures results are unique"""
    seen = set()
    for x in xs:
        if x not in seen:
            seen.add(x)
            yield x


def search_arxiv(query: str, n: int = 5) -> Iterable[ArxivResource]:
    """Searches arXiv and yields `n` ArxivResource, ordered by relevance."""

    client:      arxiv.Client = arxiv.Client()
    search_call: arxiv.Search = arxiv.Search(
        query=query, max_results=n, sort_by=arxiv.SortCriterion.Relevance
    )

    for res in client.results(search_call):
        yield ArxivResource(
            title=res.title.strip(),
            url=res.entry_id,
            description=res.summary.strip()[:200] + "..." if res.summary else None
        )


def get_resources(query: str, n: int = 5) -> Iterable[ArxivResource]:
    return deduplicate(search_arxiv(query=query, n=n))


if __name__ == "__main__":
    q = input("Search Arxiv for:\n")
    print("\nFound resources:\n")
    for r in get_resources(q, 10):
        print(f"{r.title}\n{r.url}\n{(r.description) if r.description else '(no abstract)'}\n")



