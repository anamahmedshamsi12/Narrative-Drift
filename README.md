# Narrative Drift

Narrative Drift is a local Python project that analyzes how social media narratives evolve over time. It clusters posts into narratives, builds a user-to-narrative graph, and provides a Streamlit dashboard for exploration.

## Project Structure

```
data/        # Input CSVs
src/         # Pipeline modules
app/         # Streamlit dashboard
artifacts/   # Generated outputs
scripts/     # Pipeline runners
```

## Requirements

- Python 3.10+
- pandas, NumPy
- sentence-transformers
- scikit-learn
- NetworkX
- Plotly
- Streamlit

Install dependencies:

```bash
pip install -r requirements.txt
```

## Input Data

Provide a CSV with at least the following columns:

- `post_id`
- `user`
- `timestamp`
- `text`

Place sample files in `data/`.

## Run the Pipeline

```bash
python scripts/run_pipeline.py --input data/your_posts.csv --clusters 8
```

Outputs are saved to `artifacts/`:

- `embeddings.npy`
- `clusters.csv`
- `narrative_graph.graphml`
- `centrality.csv`
- `influencers.csv`

## Run the Dashboard

```bash
streamlit run app/streamlit_app.py
```

The dashboard includes:

- Narrative volume over time
- Interactive user/narrative network graph
- Top influencers by graph centrality
- Example posts from each cluster

## Run Tests

```bash
python -m unittest discover -s tests -v
```
