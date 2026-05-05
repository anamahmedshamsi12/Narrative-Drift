"""Text cleaning utilities for Narrative Drift."""

from __future__ import annotations

import re
from typing import Iterable

import pandas as pd

URL_PATTERN = re.compile(r"https?://\S+|www\.\S+")
WHITESPACE_PATTERN = re.compile(r"\s+")


def clean_text(value: str) -> str:
    if not isinstance(value, str):
        return ""
    value = URL_PATTERN.sub("", value)
    value = WHITESPACE_PATTERN.sub(" ", value)
    return value.strip()


def clean_text_series(series: Iterable[str]) -> pd.Series:
    return pd.Series((clean_text(text) for text in series))


def clean_posts(posts: pd.DataFrame) -> pd.DataFrame:
    posts = posts.copy()
    posts["text_clean"] = clean_text_series(posts["text"])
    posts["timestamp"] = pd.to_datetime(posts["timestamp"], errors="coerce")
    return posts
