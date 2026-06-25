"""
Sentence embedding generation for Narrative Drift.
"""

from __future__ import annotations

from typing import Iterable, List

import numpy as np
from sentence_transformers import SentenceTransformer

DEFAULT_MODEL = "all-MiniLM-L6-v2"

# Cache the model so we don't reload it 500 times like amateurs
_MODEL_CACHE: dict[str, SentenceTransformer] = {}


def _get_model(model_name: str) -> SentenceTransformer:
    if model_name not in _MODEL_CACHE:
        _MODEL_CACHE[model_name] = SentenceTransformer(model_name)
    return _MODEL_CACHE[model_name]


def embed_texts(texts: Iterable[str], model_name: str = DEFAULT_MODEL) -> np.ndarray:
    """
    Generate sentence embeddings for a list of texts.

    Args:
        texts: Iterable of text strings
        model_name: Hugging Face model name

    Returns:
        NumPy array of shape (n_texts, embedding_dim)
    """
    texts_list: List[str] = [str(t) for t in texts if str(t).strip()]

    if not texts_list:
        raise ValueError("No valid text provided for embedding.")

    model = _get_model(model_name)

    embeddings = model.encode(
        texts_list,
        show_progress_bar=True,
    )

    return np.asarray(embeddings)
