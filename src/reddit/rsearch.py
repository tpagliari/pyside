import os
import re
import numpy
from dotenv import load_dotenv
from typing import Sequence, Tuple, List

from praw import Reddit # type: ignore
from praw.models import Submission, Subreddit # type: ignore
from torch import Tensor, cosine_similarity

# internal lib
from lib import deadlink
from embeddings import SemanticIndex

# To start simple, define some known subreddits
EDU_SUBREDDITS = [
    "askscience", "Physics", "learnmath", "learnprogramming", "AskAcademia",
    "computerscience", "math", "MachineLearning", "History", "philosophy", "LanguageLearning",
    "biology", "chemistry", "neuro", "Psychology", "Datacamp", "datascience", "AskHistorians"
]


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

    posts: List[Submission] = [
        post for post in subreddit.search(query_new, sort="relevance", limit=(3 * n))
    ]
    return sorted(posts, key=lambda p: scoring(query_new, p), reverse=True)[:n]


def scoring(query: str, post: Submission) -> float:
    """Return a semantic similarity score between query and post text.

    TODO: should be moved in the embeddings library
    """
    text: str = post.title + ": " + post.selftext
    etext: Tensor = semantic.model.encode(text, convert_to_tensor=True)
    equery: Tensor = semantic.model.encode(query, convert_to_tensor=True) # TODO: we are building this embedding every time we assign a score, nonsense
    similarity: Tensor = cosine_similarity(etext, equery, dim=0)
    return similarity.item()


def get_resources(post: Submission) -> List[str]:
    """Get resources (links only at the moment) from a post.
    Internally, it checks that the link is not dead.
    """
    re_url: str = r'(https?://\S+)'
    
    post.comments.replace_more(limit=0)
    comments : list = post.comments.list()
    
    resources = set()
    for comment in sorted(comments, key=lambda c: c.score, reverse=True):
        urls = re.findall(re_url, comment.body)
        for url in urls:
            clean_url = url.strip(").,]")
            if not deadlink(clean_url, 3):
                resources.add(clean_url)
        #if "book" in comment.body.lower() or "course" in comment.body.lower():
        #    resources.add(comment.body.strip())

    return list(resources) 


def get_all_resources(query: str) -> list[str]:
    rinstance : Reddit = reddit_client()
    subreddits : list[str] = get_subreddits(query, 2)

    # Log info while developing
    print("I am using these subreddits (semantic score):\n")
    print(subreddits)

    all_resources = []
    for sub in subreddits:
        posts : list[Submission] = get_posts(rinstance, sub, query, 3)
        for post in posts:
            links : list[str] = get_resources(post)
            all_resources.extend(links)

    return all_resources


if __name__ == "__main__":
    # Run once to build the index
    first_time = False
    if first_time:
        semantic.build(EDU_SUBREDDITS)

    user_query : str = input("What do you want to learn?\n")
    links : List[str]= get_all_resources(query=user_query)
    print("Got these:\n", links)
