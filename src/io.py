"""Input/output helpers for Narrative Drift."""

from __future__ import annotations

import pandas as pd

from .preprocess import clean_posts

REQUIRED_COLUMNS = {"post_id", "user", "timestamp", "text"}


def load_posts(csv_path: str) -> pd.DataFrame:
    posts = pd.read_csv(csv_path)
    missing = REQUIRED_COLUMNS - set(posts.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    return clean_posts(posts)
