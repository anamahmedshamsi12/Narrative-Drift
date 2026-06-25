"""
Preprocessing utilities for Narrative Drift.

Responsibilities:
- Validate required columns
- Clean text (remove URLs, normalize whitespace)
- Parse timestamps
- Optionally drop rows with empty text
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

import pandas as pd

REQUIRED_COLUMNS = {"post_id", "user", "timestamp", "text"}

# Remove http(s)://... and www....
_URL_RE = re.compile(r"(https?://\S+|www\.\S+)", flags=re.IGNORECASE)

# Collapse any whitespace runs (spaces/tabs/newlines)
_WS_RE = re.compile(r"\s+")


@dataclass(frozen=True)
class PreprocessConfig:
    strip_urls: bool = True
    normalize_whitespace: bool = True
    drop_empty_text: bool = True

    # Timestamp parsing
    timestamp_utc: bool = True   # parse as timezone-aware UTC when possible
    coerce_timestamp: bool = True  # invalid timestamps become NaT instead of raising


def _clean_one_text(text: object, *, strip_urls: bool, normalize_ws: bool) -> str:
    """
    Clean a single text value safely.
    """
    if not isinstance(text, str):
        text = "" if text is None else str(text)

    if strip_urls:
        text = _URL_RE.sub("", text)

    if normalize_ws:
        text = _WS_RE.sub(" ", text).strip()

    return text


def clean_text_series(
    s: pd.Series,
    *,
    strip_urls: bool = True,
    normalize_whitespace: bool = True,
) -> pd.Series:
    """
    Vectorized cleaning for a pandas Series.
    """
    s = s.fillna("").astype(str)
    if strip_urls:
        s = s.str.replace(_URL_RE, "", regex=True)
    if normalize_whitespace:
        s = s.str.replace(_WS_RE, " ", regex=True).str.strip()
    return s


def preprocess_posts(df: pd.DataFrame, config: Optional[PreprocessConfig] = None) -> pd.DataFrame:
    """
    Preprocess and return a NEW DataFrame (does not mutate input).

    Output schema includes the same required columns:
      post_id (str), user (str), timestamp (datetime), text (cleaned str)
    """
    cfg = config or PreprocessConfig()

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}. Found: {list(df.columns)}")

    out = df.copy()

    # Standardize types for stability
    out["post_id"] = out["post_id"].astype(str)
    out["user"] = out["user"].astype(str)

    # Clean text IN PLACE (no text_clean column)
    out["text"] = clean_text_series(
        out["text"],
        strip_urls=cfg.strip_urls,
        normalize_whitespace=cfg.normalize_whitespace,
    )

    # Parse timestamps
    errors = "coerce" if cfg.coerce_timestamp else "raise"
    out["timestamp"] = pd.to_datetime(out["timestamp"], errors=errors, utc=cfg.timestamp_utc)

    # Drop empty text rows if requested
    if cfg.drop_empty_text:
        out = out[out["text"].str.len() > 0].copy()

    return out
