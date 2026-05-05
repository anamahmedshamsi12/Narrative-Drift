"""Streamlit dashboard for Narrative Drift."""

from __future__ import annotations

from pathlib import Path

import networkx as nx
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


ARTIFACTS_DIR = Path("artifacts")


@st.cache_data
def load_posts() -> pd.DataFrame:
    clusters_path = ARTIFACTS_DIR / "clusters.csv"
    return pd.read_csv(clusters_path, parse_dates=["timestamp"])


@st.cache_data
def load_centrality() -> pd.DataFrame:
    path = ARTIFACTS_DIR / "centrality.csv"
    return pd.read_csv(path)


@st.cache_data
def load_graph() -> nx.Graph:
    graph_path = ARTIFACTS_DIR / "narrative_graph.graphml"
    return nx.read_graphml(graph_path)


st.set_page_config(page_title="Narrative Drift Dashboard", layout="wide")

st.title("Narrative Drift Dashboard")

if not (ARTIFACTS_DIR / "clusters.csv").exists():
    st.warning("Run the pipeline first to generate artifacts.")
    st.stop()

posts = load_posts()
centrality = load_centrality()

st.subheader("Narrative Clusters Over Time")

posts["date"] = posts["timestamp"].dt.date
cluster_timeline = (
    posts.groupby(["date", "cluster"])["post_id"]
    .count()
    .reset_index(name="post_count")
)

fig_timeline = px.bar(
    cluster_timeline,
    x="date",
    y="post_count",
    color="cluster",
    title="Narrative Volume by Day",
    labels={"post_count": "Posts"},
)

st.plotly_chart(fig_timeline, use_container_width=True)

st.subheader("Narrative Network")

graph = load_graph()
layout = nx.spring_layout(graph, seed=42)

edge_x = []
edge_y = []
for source, target in graph.edges():
    x0, y0 = layout[source]
    x1, y1 = layout[target]
    edge_x += [x0, x1, None]
    edge_y += [y0, y1, None]

edge_trace = go.Scatter(
    x=edge_x,
    y=edge_y,
    line=dict(width=0.5, color="#888"),
    hoverinfo="none",
    mode="lines",
)

node_x = []
node_y = []
node_text = []
node_color = []
for node, data in graph.nodes(data=True):
    x, y = layout[node]
    node_x.append(x)
    node_y.append(y)
    node_text.append(node)
    node_type = data.get("node_type", "unknown")
    node_color.append("#1f77b4" if node_type == "user" else "#ff7f0e")

node_trace = go.Scatter(
    x=node_x,
    y=node_y,
    mode="markers",
    hoverinfo="text",
    text=node_text,
    marker=dict(
        color=node_color,
        size=10,
        line_width=0.5,
    ),
)

fig_network = go.Figure(data=[edge_trace, node_trace])
fig_network.update_layout(
    title="User-Cluster Network",
    showlegend=False,
    margin=dict(l=10, r=10, t=40, b=10),
    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
)

st.plotly_chart(fig_network, use_container_width=True)

st.subheader("Top Influencers")

influencers = centrality[centrality["node"].str.startswith("user:")].copy()
influencers["user"] = influencers["node"].str.replace("user:", "", regex=False)

st.dataframe(
    influencers[["user", "degree", "betweenness"]].sort_values("degree", ascending=False).head(10),
    use_container_width=True,
)

st.subheader("Example Posts by Cluster")

cluster_id = st.selectbox("Cluster", sorted(posts["cluster"].unique()))
examples = posts[posts["cluster"] == cluster_id][["post_id", "user", "text"]].head(5)

for _, row in examples.iterrows():
    st.markdown(f"**{row['user']}** ({row['post_id']}): {row['text']}")
