"""
Streamlit dashboard for Narrative Drift.

Reads pipeline artifacts from /artifacts and visualizes:
- Narrative cluster counts over time
- User<->Cluster interaction graph
- Top influencers by centrality
- Example posts per cluster
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional, Tuple

import networkx as nx
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.graph_builder import compute_centrality  # uses your cleaned helper


ARTIFACTS_DEFAULT = Path("artifacts")


def _load_metadata(artifacts_dir: Path) -> dict:
    meta_path = artifacts_dir / "metadata.json"
    if meta_path.exists():
        try:
            return json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _load_posts(artifacts_dir: Path) -> pd.DataFrame:
    pq = artifacts_dir / "posts_with_clusters.parquet"
    csv = artifacts_dir / "posts_with_clusters.csv"

    if pq.exists():
        return pd.read_parquet(pq)
    if csv.exists():
        return pd.read_csv(csv)

    raise FileNotFoundError(
        f"Could not find posts_with_clusters.parquet or posts_with_clusters.csv in {artifacts_dir.resolve()}"
    )


def _load_graph(artifacts_dir: Path) -> nx.Graph:
    graphml = artifacts_dir / "graph.graphml"
    gpickle = artifacts_dir / "graph.gpickle"

    if graphml.exists():
        return nx.read_graphml(graphml)
    if gpickle.exists():
        return nx.read_gpickle(gpickle)

    raise FileNotFoundError(
        f"Could not find graph.graphml or graph.gpickle in {artifacts_dir.resolve()}"
    )


def _coerce_timestamp(df: pd.DataFrame) -> pd.DataFrame:
    if "timestamp" in df.columns:
        df = df.copy()
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce", utc=True)
    return df


def _cluster_timeline(df: pd.DataFrame, freq: str = "D") -> go.Figure:
    """
    Plot cluster counts over time.
    """
    df = _coerce_timestamp(df)
    df = df.dropna(subset=["timestamp"]).copy()

    if df.empty:
        return go.Figure().update_layout(title="No valid timestamps to plot.")

    # bucket timestamps
    df["bucket"] = df["timestamp"].dt.to_period(freq).dt.to_timestamp()

    counts = (
        df.groupby(["bucket", "cluster"])
        .size()
        .reset_index(name="count")
        .sort_values("bucket")
    )

    fig = px.bar(
        counts,
        x="bucket",
        y="count",
        color="cluster",
        title="Narrative clusters over time",
        labels={"bucket": "Time", "count": "Posts"},
    )
    fig.update_layout(barmode="stack")
    return fig


def _graph_plot(G: nx.Graph) -> go.Figure:
    """
    Render a simple interactive network plot.
    """
    if G.number_of_nodes() == 0:
        return go.Figure().update_layout(title="Graph is empty.")

    # Spring layout is fine for small/medium graphs
    pos = nx.spring_layout(G, seed=42)

    # Build edges
    edge_x = []
    edge_y = []
    weights = []
    for u, v, data in G.edges(data=True):
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]
        weights.append(data.get("weight", 1))

    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        mode="lines",
        hoverinfo="none",
    )

    # Build nodes
    node_x = []
    node_y = []
    node_text = []
    node_type = []

    for n, data in G.nodes(data=True):
        x, y = pos[n]
        node_x.append(x)
        node_y.append(y)
        node_text.append(n)
        node_type.append(data.get("node_type", "unknown"))

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers",
        hoverinfo="text",
        text=node_text,
        marker=dict(size=10),
    )

    fig = go.Figure(data=[edge_trace, node_trace])
    fig.update_layout(
        title="User ↔ Cluster narrative graph",
        showlegend=False,
        margin=dict(l=10, r=10, t=40, b=10),
    )
    return fig


def _examples_by_cluster(df: pd.DataFrame, cluster: int | str, k: int = 8) -> pd.DataFrame:
    subset = df[df["cluster"] == cluster].copy()
    subset = subset.sort_values("timestamp") if "timestamp" in subset.columns else subset
    cols = [c for c in ["timestamp", "user", "text", "post_id"] if c in subset.columns]
    return subset[cols].head(k)


def main() -> None:
    st.set_page_config(page_title="Narrative Drift", layout="wide")

    st.title("Narrative Drift")
    st.caption("Because social media narratives never stay stable, and neither do people.")

    with st.sidebar:
        st.header("Artifacts")
        artifacts_dir = Path(st.text_input("Artifacts directory", str(ARTIFACTS_DEFAULT))).resolve()

        st.subheader("Timeline settings")
        freq = st.selectbox("Bucket size", options=["D", "W", "M"], index=0)
        examples_k = st.slider("Example posts per cluster", 3, 20, 8)

    # Load artifacts
    try:
        meta = _load_metadata(artifacts_dir)
        df = _load_posts(artifacts_dir)
        G = _load_graph(artifacts_dir)
    except Exception as e:
        st.error(f"Failed to load artifacts: {e}")
        st.stop()

    # Basic cleanup
    df = _coerce_timestamp(df)

    # Top line stats
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Posts", len(df))
    c2.metric("Clusters", df["cluster"].nunique() if "cluster" in df.columns else 0)
    c3.metric("Graph nodes", G.number_of_nodes())
    c4.metric("Graph edges", G.number_of_edges())

    if meta.get("config"):
        with st.expander("Pipeline config"):
            st.json(meta["config"])

    st.divider()

    # Layout: timeline + graph
    left, right = st.columns([1.2, 1.0], gap="large")

    with left:
        st.plotly_chart(_cluster_timeline(df, freq=freq), use_container_width=True)

    with right:
        st.plotly_chart(_graph_plot(G), use_container_width=True)

    st.divider()

    # Influencers and examples
    st.subheader("Influencers & narrative examples")

    try:
        centrality_df, influencers_df = compute_centrality(G)
    except Exception as e:
        st.warning(f"Centrality computation failed: {e}")
        centrality_df = pd.DataFrame()
        influencers_df = pd.DataFrame()

    colA, colB = st.columns([1.0, 1.2], gap="large")

    with colA:
        st.markdown("Top influencers (by degree centrality)")
        if influencers_df.empty:
            st.info("No influencer data available.")
        else:
            show_cols = [c for c in ["user", "degree", "betweenness"] if c in influencers_df.columns]
            st.dataframe(influencers_df[show_cols].head(20), use_container_width=True)

    with colB:
        if "cluster" not in df.columns:
            st.info("No cluster column found in posts.")
            return

        clusters = sorted(df["cluster"].dropna().unique().tolist())
        chosen = st.selectbox("Pick a cluster to inspect", clusters)

        st.markdown("Example posts in this cluster")
        ex = _examples_by_cluster(df, chosen, k=examples_k)
        if ex.empty:
            st.info("No posts found for this cluster.")
        else:
            st.dataframe(ex, use_container_width=True)


if __name__ == "__main__":
    main()
