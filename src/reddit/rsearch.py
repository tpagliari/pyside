import os
import re

from dotenv import load_dotenv
from typing import List

from praw import Reddit # type: ignore
from praw.models import Submission, Subreddit # type: ignore
from torch import Tensor, cosine_similarity
from concurrent.futures import ThreadPoolExecutor

# internal lib
from .lib import filter_live_urls
from .embeddings import SemanticIndex
from .const import EDU_SUBREDDITS


def reddit_client() -> Reddit:
    """Create a read-only reddit instance."""
    load_dotenv()
    reddit = Reddit(
        client_id = os.getenv("REDDIT_CLIENT_ID"),
        client_secret = os.getenv("REDDIT_CLIENT_SECRET"),
        user_agent = os.getenv("REDDIT_USER_AGENT")
    )
    return reddit

semantic = SemanticIndex()

def get_subreddits(query: str, n: int) -> List[str]:
    """Returns a list of n subreddits that have high semantic similarity
    with the user query.
    """
    results = semantic.query(query, top_k=n)
    return [sub for sub, _ in results]


def get_posts(rinstance: Reddit, sub: str, query: str, n: int) -> List[Submission]:
    """
    Given a subreddit, extract n post that match the query using reddit search.

    TODO: Find a *fast* way to further rank posts by semantic similarity to the query. We can't build
    another faiss index while running (?), but we can't either rely solely on reddit search. 
    """
    subreddit: Subreddit = rinstance.subreddit(sub)

    query_new: str = "Resources to learn " + query
    equery: Tensor = semantic.model.encode(query_new, convert_to_tensor=True)
    
    posts: List[Submission] = [
        post for post in subreddit.search(query_new, sort="relevance", limit=(3 * n))
    ]
    return sorted(posts, key=lambda p: scoring(equery, p), reverse=True)[:n]


def scoring(equery: Tensor, post: Submission) -> float:
    """Score a single post against pre-computed query embedding.
    """
    text: str = post.title + ": " + post.selftext
    etext: Tensor = semantic.model.encode(text, convert_to_tensor=True)
    similarity: Tensor = cosine_similarity(etext, equery, dim=0)
    return similarity.item()


def get_resources(post: Submission) -> List[str]:
    """Get resources (links only at the moment) from a post.
    Internally, it checks that the link is not dead.

    TODO: even suggested books in the comments should be retrieved.
    """
    re_url: str = r'(https?://\S+)'
    
    post.comments.replace_more(limit=1) # Expands only the top level of MoreComments
    comments : list = post.comments.list()[:50] # cap comments checked

    # Collect all URLs first
    urls = (url.strip(").,]")
            for comment in sorted(comments, key=lambda c: c.score, reverse=True)
            for url in re.findall(re_url, comment.body))
    
    # Filter in parallel
    # TODO: I think here we are losing ordering of links, order is important to have best links ontop!!
    return list(filter_live_urls(set(urls), timeout=3, max_workers=10))


def get_all_resources(query: str, no_subreddits: int = 2, no_posts: int = 4) -> list[str]:
    """
    Main entrance point, where:
      - query: user search term
      - no_subreddits: number of subreddits you want for the rsearch
      - no_posts: number of posts per subreddit to use as links source
      - returns the list of links obtained
    """
    rinstance : Reddit = reddit_client()
    subreddits : list[str] = get_subreddits(query, no_subreddits)

    # Log info while developing
    print(f"I am using these subreddits (semantic score):\n{subreddits}\n\n")

    def fetch(sub: str) -> list[str]:
        """Helper function to fetch posts per subreddit and extract
        resources (links).
        """
        posts: list[Submission] = get_posts(rinstance, sub, query, no_posts)
        resources = []
        for post in posts:
            links: list[str] = get_resources(post)
            resources.extend(links)
        return resources
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(fetch, subreddits)
    
    return [link for links in results for link in links]



if __name__ == "__main__":
    # Run once to build the index
    first_time = False
    if first_time:
        import sys
        semantic.build(EDU_SUBREDDITS)
        print("Completed embedding of educational subreddits")
        sys.exit(0)

    user_query : str = input("What do you want to learn?\n")
    links : List[str]= get_all_resources(query=user_query)
    print("Got these:\n", links)
