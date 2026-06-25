"""
Input/output helpers for Narrative Drift.

Responsibilities:
- Load CSV files
- Validate required columns
- Delegate cleaning to preprocess.py
"""

from __future__ import annotations

from pathlib import Path
from typing import Union

import pandas as pd

from .preprocess import preprocess_posts

REQUIRED_COLUMNS = {"post_id", "user", "timestamp", "text"}

PathLike = Union[str, Path]


def load_posts_csv(csv_path: PathLike) -> pd.DataFrame:
    """
    Load a CSV file and return a cleaned posts DataFrame.

    Required columns:
      - post_id
      - user
      - timestamp
      - text
    """
    path = Path(csv_path)

    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path.resolve()}")

    posts = pd.read_csv(path)

    missing = REQUIRED_COLUMNS - set(posts.columns)
    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(missing)}. "
            f"Found columns: {list(posts.columns)}"
        )

    return preprocess_posts(posts)

