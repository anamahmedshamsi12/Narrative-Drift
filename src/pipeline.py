"""
Pipeline orchestrator for Narrative Drift.

Responsibilities:
- Load + preprocess posts
- Generate embeddings
- Cluster into narratives
- Build user<->cluster graph
- Save artifacts to disk
"""

from __future__ import annotations

import json
import pickle
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import networkx as nx

from .data_loader import load_posts
from .embeddings import embed_texts
from .clustering import cluster_embeddings
from .graph_builder import build_graph


@dataclass(frozen=True)
class PipelineConfig:
    # Embeddings
    model_name: str = "all-MiniLM-L6-v2"

    # Clustering (KMeans for now)
    n_clusters: int = 8
    random_state: int = 42

    # Columns
    text_col: str = "text"
    timestamp_col: str = "timestamp"
    user_col: str = "user"
    post_id_col: str = "post_id"
    cluster_col: str = "cluster"

    # Output filenames
    posts_out: str = "posts_with_clusters.parquet"
    embeddings_out: str = "embeddings.npy"
    cluster_model_out: str = "cluster_model.pkl"
    graph_out: str = "graph.graphml"
    metadata_out: str = "metadata.json"


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _safe_parquet_or_csv(df: pd.DataFrame, path: Path) -> Path:
    """
    Save as parquet if possible; fall back to CSV. Returns the written path.
    """
    try:
        df.to_parquet(path, index=False)
        return path
    except Exception:
        csv_path = path.with_suffix(".csv")
        df.to_csv(csv_path, index=False)
        return csv_path


def run_pipeline(
    input_csv: str | Path,
    artifacts_dir: str | Path = "artifacts",
    config: Optional[PipelineConfig] = None,
) -> dict:
    """
    Run the Narrative Drift pipeline end-to-end.

    Returns:
        metadata dict including artifact paths and basic stats.
    """
    cfg = config or PipelineConfig()
    artifacts_path = Path(artifacts_dir)
    _ensure_dir(artifacts_path)

    # 1) Load posts (cleaned by io/preprocess via data_loader wrapper)
    df = load_posts(input_csv)

    # Defensive checks
    required_cols = [cfg.post_id_col, cfg.user_col, cfg.timestamp_col, cfg.text_col]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(
            f"Pipeline expected columns {missing} but they were missing. Found: {list(df.columns)}"
        )

    # Drop empty text rows (belt + suspenders)
    df = df[df[cfg.text_col].astype(str).str.len() > 0].copy()

    # 2) Generate embeddings
    texts = df[cfg.text_col].astype(str).tolist()
    embeddings = embed_texts(texts, model_name=cfg.model_name)
    embeddings = np.asarray(embeddings)

    if embeddings.ndim != 2 or embeddings.shape[0] != len(df):
        raise ValueError(
            f"Embeddings shape {embeddings.shape} does not match expected (n_posts, dim)=({len(df)}, dim)."
        )

    # 3) Cluster embeddings (returns labels + fitted model)
    labels, cluster_model = cluster_embeddings(
        embeddings,
        n_clusters=cfg.n_clusters,
        random_state=cfg.random_state,
    )

    labels = np.asarray(labels)
    if labels.shape[0] != len(df):
        raise ValueError(f"Cluster labels count ({labels.shape[0]}) != posts row count ({len(df)}).")

    df[cfg.cluster_col] = labels

    # 4) Build graph (user <-> cluster weighted edges)
    G = build_graph(df, cluster_col=cfg.cluster_col, user_col=cfg.user_col)
    if not isinstance(G, nx.Graph):
        raise TypeError("build_graph() must return a networkx Graph.")

    # 5) Save artifacts
    posts_path = artifacts_path / cfg.posts_out
    embeddings_path = artifacts_path / cfg.embeddings_out
    cluster_model_path = artifacts_path / cfg.cluster_model_out
    graph_path = artifacts_path / cfg.graph_out
    metadata_path = artifacts_path / cfg.metadata_out

    written_posts_path = _safe_parquet_or_csv(df, posts_path)
    np.save(embeddings_path, embeddings)

    # Save clustering model for reproducibility
    with open(cluster_model_path, "wb") as f:
        pickle.dump(cluster_model, f)

    # GraphML is a nice interoperable default, but can fail on some attribute types
    written_graph_path: Path
    try:
        nx.write_graphml(G, graph_path)
        written_graph_path = graph_path
    except Exception:
        gp_path = graph_path.with_suffix(".gpickle")
        nx.write_gpickle(G, gp_path)
        written_graph_path = gp_path

    metadata = {
        "config": asdict(cfg),
        "rows": int(len(df)),
        "num_clusters": int(df[cfg.cluster_col].nunique()),
        "artifacts": {
            "posts": str(written_posts_path),
            "embeddings": str(embeddings_path),
            "cluster_model": str(cluster_model_path),
            "graph": str(written_graph_path),
        },
    }

    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata
