"""
Data loading utilities for Narrative Drift.

This module stays as the stable entry point for loading post data across the codebase.
Actual CSV I/O + preprocessing live in src/io.py and src/preprocess.py.
"""

from __future__ import annotations

from pathlib import Path
from typing import Union

import pandas as pd

from .io import load_posts_csv


PathLike = Union[str, Path]


def load_posts(csv_path: PathLike) -> pd.DataFrame:
    """
    Load and return a cleaned posts DataFrame with required columns:
      - post_id
      - user
      - timestamp
      - text

    Cleaning includes URL removal, whitespace normalization, and timestamp parsing.
    """
    return load_posts_csv(csv_path)


# Backward-compatible alias (useful if other modules still import load_data)
def load_data(csv_path: PathLike) -> pd.DataFrame:
    return load_posts(csv_path)

