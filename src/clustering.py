"""
Clustering utilities for Narrative Drift.

Currently supports KMeans clustering on normalized embeddings.
"""

from __future__ import annotations

from typing import Tuple

import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import normalize

DEFAULT_N_CLUSTERS = 8
DEFAULT_RANDOM_STATE = 42


def cluster_embeddings(
    embeddings: np.ndarray,
    n_clusters: int = DEFAULT_N_CLUSTERS,
    random_state: int = DEFAULT_RANDOM_STATE,
) -> Tuple[np.ndarray, KMeans]:
    """
    Cluster sentence embeddings into narrative groups using KMeans.

    Args:
        embeddings: Array of shape (n_samples, embedding_dim)
        n_clusters: Number of clusters to form
        random_state: Random seed for reproducibility

    Returns:
        labels: Cluster label for each embedding
        model: Fitted KMeans model
    """
    if embeddings is None or embeddings.size == 0:
        raise ValueError("Embeddings array is empty or None.")

    if embeddings.ndim != 2:
        raise ValueError(
            f"Embeddings must be 2D (n_samples, dim). Got shape {embeddings.shape}"
        )

    # Normalize embeddings so KMeans behaves nicely
    normalized = normalize(embeddings)

    model = KMeans(
        n_clusters=n_clusters,
        random_state=random_state,
        n_init="auto",
    )

    labels = model.fit_predict(normalized)

    return labels, model
