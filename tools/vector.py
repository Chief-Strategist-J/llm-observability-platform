# tools/vector.py
from typing import List, Tuple
from llm_client import embeddings
import math

# Minimal seed corpus (extend anytime)
_MOVIES: List[Tuple[str, str]] = [
    ("The Matrix (1999)", "A hacker discovers reality is a simulation and joins rebels to free humanity."),
    ("Inception (2010)", "A thief who steals corporate secrets through dream-sharing is given a chance at redemption."),
    ("Interstellar (2014)", "Explorers travel through a wormhole in space to ensure humanity's survival."),
    ("The Dark Knight (2008)", "Batman faces the Joker, who unleashes chaos on Gotham."),
    ("The Social Network (2010)", "The founding of Facebook and the ensuing legal disputes."),
]

# Pre-compute embeddings (lazy cache)
_vectors = None

def _cosine(a, b):
    dot = sum(x*y for x, y in zip(a, b))
    na = math.sqrt(sum(x*x for x in a))
    nb = math.sqrt(sum(y*y for y in b))
    return dot / (na * nb + 1e-9)

def _ensure_index():
    global _vectors
    if _vectors is None:
        _vectors = [embeddings.embed_query(title + " " + plot) for title, plot in _MOVIES]

def get_movie_plot(query: str) -> str:
    """
    Vector similarity over a tiny seed corpus.
    Returns a short formatted list of top matches as context.
    """
    _ensure_index()
    qv = embeddings.embed_query(query)
    scored = []
    for (title, plot), vec in zip(_MOVIES, _vectors):
        scored.append((_cosine(qv, vec), title, plot))
    scored.sort(reverse=True)
    top = scored[:3]
    if not top:
        return "No matches."
    lines = [f"- {t}: {p}" for _, t, p in top]
    return "Top plots (approximate):\n" + "\n".join(lines)
