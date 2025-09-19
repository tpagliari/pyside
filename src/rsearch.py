import os
import re
from praw import Reddit # type: ignore
from praw.models import Submission, Subreddit # type: ignore
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from torch import Tensor, cosine_similarity, topk

# internal lib
from lib import deadlink


# This model maps sentences & paragraphs to a 384 dimensional dense vector space
# and can be used for tasks like clustering or semantic search.
MODEL = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

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


def get_subreddits(query: str, n: int) -> list[str]:
    """Returns a list of n subreddits that have high semantic similarity
    with the user query.
    """
    embeddings_subreddits : Tensor = MODEL.encode(EDU_SUBREDDITS, convert_to_tensor=True)
    embedding_query       : Tensor = MODEL.encode(query, convert_to_tensor=True)
    
    similarities : Tensor = cosine_similarity(embeddings_subreddits, embedding_query)  
    indeces : Tensor = topk(similarities, n)[1]
    
    return [EDU_SUBREDDITS[i] for _, i in enumerate(indeces)]


def get_posts(rinstance: Reddit, sub: str, query: str, n: int) -> list[Submission]:
    """Given a subreddit, extract n post that match the query using reddit search.
    Internally, it ranks them by semantic similarity to the query.
    """
    subreddit : Subreddit = rinstance.subreddit(sub)
    query_new : str = "Suggest me valuable resources to learn " + query
    
    posts : list[Submission] = [
        post for post in subreddit.search(query_new, sort="relevance", limit=(3*n))
    ]
    return sorted(posts, key=lambda p: scoring(query_new, p), reverse=True)[:n]


def scoring(query: str, post: Submission) -> float:
    """Return a semantic similarity score between query and post text.
    """
    text  : str = post.title + ": " + post.selftext
    etext : Tensor = MODEL.encode(text, convert_to_tensor=True)
    equery: Tensor = MODEL.encode(query, convert_to_tensor=True)
    similarity : Tensor = cosine_similarity(etext, equery, dim=0)
    return similarity.item()


def get_resources(post: Submission) -> list[str]:
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

    all_resources = []
    for sub in subreddits:
        posts : list[Submission] = get_posts(rinstance, sub, query, 3)
        for post in posts:
            links : list[str] = get_resources(post)
            all_resources.extend(links)

    return all_resources


if __name__ == "__main__":
    user_query : str = input("What do you want to learn?\n")
    links : list[str]= get_all_resources(query=user_query)
    print("Got these:\n", links)
