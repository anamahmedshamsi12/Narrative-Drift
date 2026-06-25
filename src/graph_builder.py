"""
Graph construction for narrative and user interactions.

Builds a bipartite-ish graph:
- User nodes:   "user:<username>"
- Cluster nodes:"cluster_<cluster_id>"

Edges connect users to clusters with a weight = number of posts by that user in that cluster.
Also includes centrality helpers for influencer ranking.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import networkx as nx
import pandas as pd

USER_PREFIX = "user:"
CLUSTER_PREFIX = "cluster_"


@dataclass(frozen=True)
class GraphConfig:
    user_col: str = "user"
    cluster_col: str = "cluster"


def build_narrative_graph(posts: pd.DataFrame, config: GraphConfig | None = None) -> nx.Graph:
    """
    Build a graph connecting users to narrative clusters.

    Args:
        posts: DataFrame containing at least user and cluster columns.
        config: Column configuration.

    Returns:
        networkx.Graph with weighted edges.
    """
    cfg = config or GraphConfig()

    missing = [c for c in (cfg.user_col, cfg.cluster_col) if c not in posts.columns]
    if missing:
        raise ValueError(
            f"build_narrative_graph: missing columns {missing}. Found: {list(posts.columns)}"
        )

    graph = nx.Graph()

    # Use itertuples for speed and fewer pandas dtype surprises
    for row in posts[[cfg.user_col, cfg.cluster_col]].itertuples(index=False, name=None):
        user_val, cluster_val = row

        user_node = f"{USER_PREFIX}{str(user_val)}"
        cluster_node = f"{CLUSTER_PREFIX}{str(cluster_val)}"

        if not graph.has_node(user_node):
            graph.add_node(user_node, node_type="user")
        if not graph.has_node(cluster_node):
            graph.add_node(cluster_node, node_type="cluster")

        if graph.has_edge(user_node, cluster_node):
            graph[user_node][cluster_node]["weight"] += 1
        else:
            graph.add_edge(user_node, cluster_node, weight=1)

    return graph


def compute_centrality(graph: nx.Graph) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Compute degree and betweenness centrality, and return:
    - centrality_df: all nodes ranked by degree
    - influencers: only user nodes, with extracted username
    """
    if graph.number_of_nodes() == 0:
        empty = pd.DataFrame(columns=["node", "degree", "betweenness"])
        influencers = pd.DataFrame(columns=["node", "degree", "betweenness", "user"])
        return empty, influencers

    degree = nx.degree_centrality(graph)
    betweenness = nx.betweenness_centrality(graph)

    centrality_df = (
        pd.DataFrame({"node": list(degree.keys()), "degree": list(degree.values())})
        .merge(
            pd.DataFrame(
                {"node": list(betweenness.keys()), "betweenness": list(betweenness.values())}
            ),
            on="node",
            how="left",
        )
        .sort_values(["degree", "betweenness"], ascending=False)
        .reset_index(drop=True)
    )

    influencers = centrality_df[centrality_df["node"].str.startswith(USER_PREFIX)].copy()
    influencers["user"] = influencers["node"].str.replace(USER_PREFIX, "", regex=False)

    return centrality_df, influencers


# ---- Compatibility aliases (so the rest of your project stops arguing with itself) ----

def build_graph(posts: pd.DataFrame, cluster_col: str = "cluster", user_col: str = "user") -> nx.Graph:
    """
    Alias used by some pipelines/apps.
    """
    return build_narrative_graph(posts, config=GraphConfig(user_col=user_col, cluster_col=cluster_col))
