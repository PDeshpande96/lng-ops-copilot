from typing import Any
from tools import search_sops


def retrieve_relevant_sops(query: str) -> list[dict[str, Any]]:
    """
    Wrapper around local SOP retrieval.
    Later this can be replaced with FAISS/embeddings without changing the agent flow.
    """
    return search_sops(query)