from __future__ import annotations
import faiss  # type: ignore
import numpy as np
from sentence_transformers import SentenceTransformer

# --- Types ---
from typing import Sequence, Tuple, List
Subreddit = str
SearchResult = Tuple[Subreddit, float]
IndexPath = str


class SemanticIndex:
    """
    Wrapper around FAISS for subreddit embeddings and semantic search.
    Provides methods for building, loading, and querying the index.
      - Default model is `all-MiniLM-L6-v2`, which maps sentences & paragraphs to
    a 384 dimensional dense vector space and can be used for tasks like clustering or semantic search.
      - Default output files are `subreddits.index` and `subredditsNames.npy`
    """

    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        index_file: IndexPath = "subreddits.index",
        names_file: str = "subredditsNames.npy") -> None:
        
        self.model: SentenceTransformer = SentenceTransformer(model_name)
        self.index_file: IndexPath = index_file
        self.names_file: str = names_file
        

    def build(self, subreddits: Sequence[Subreddit]) -> None:
        """
        Build a FAISS index from a list of subreddit names and save it.
        Embedded vectors are normalized so that cosine similarity equals L2 scalar product.

        TODO: We should add subreddit metadata to improve the semantic embedding in the vector space
        """
        embeddings: np.ndarray = self.model.encode(
            list(subreddits), convert_to_tensor=True
        ).cpu().numpy()
        faiss.normalize_L2(embeddings)

        d: int = embeddings.shape[1]
        index: faiss.Index = faiss.IndexFlatIP(d)
        index.add(embeddings)  # type: ignore

        faiss.write_index(index, self.index_file)
        np.save(self.names_file, np.array(subreddits, dtype=object))


    def load(self) -> Tuple[faiss.Index, np.ndarray]:
        """
        Load an existing FAISS index and subreddit names from disk.
        """
        index: faiss.Index = faiss.read_index(self.index_file)
        subreddits: np.ndarray = np.load(self.names_file, allow_pickle=True)
        return index, subreddits


    def query(self, query: str, top_k: int) -> List[SearchResult]:
        """
        Query the index for the most semantically similar subreddits to a given query.
        Returns a list of (subreddit, similarity_score).
        """
        index, subreddits = self.load()

        query_emb: np.ndarray = self.model.encode(
            [query], convert_to_tensor=True
        ).cpu().numpy()
        faiss.normalize_L2(query_emb)

        D: np.ndarray
        I: np.ndarray
        D, I = index.search(query_emb, top_k)  # type: ignore

        return [(str(subreddits[i]), float(D[0][j])) for j, i in enumerate(I[0])]
