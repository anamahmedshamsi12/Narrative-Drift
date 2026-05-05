from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

PANDAS_IMPORT_ERROR = None
try:
    import pandas as pd
except ModuleNotFoundError as exc:  # pragma: no cover - environment-dependent
    PANDAS_IMPORT_ERROR = exc

@unittest.skipIf(PANDAS_IMPORT_ERROR is not None, f"pandas is required: {PANDAS_IMPORT_ERROR}")
class TestPreprocess(unittest.TestCase):
    def test_clean_text_removes_urls_and_normalizes_whitespace(self) -> None:
        from src.preprocess import clean_text

        text = "Check this https://example.com   now\nplease"
        self.assertEqual(clean_text(text), "Check this now please")

    def test_clean_posts_adds_text_clean_and_parses_timestamp(self) -> None:
        from src.preprocess import clean_posts

        frame = pd.DataFrame(
            {
                "post_id": [1],
                "user": ["alice"],
                "timestamp": ["2026-01-01T10:00:00Z"],
                "text": ["hello   world"],
            }
        )
        cleaned = clean_posts(frame)
        self.assertIn("text_clean", cleaned.columns)
        self.assertEqual(cleaned.loc[0, "text_clean"], "hello world")
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(cleaned["timestamp"]))


@unittest.skipIf(PANDAS_IMPORT_ERROR is not None, f"pandas is required: {PANDAS_IMPORT_ERROR}")
class TestIO(unittest.TestCase):
    def test_load_posts_requires_columns(self) -> None:
        from src.io import load_posts

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.csv"
            pd.DataFrame({"post_id": [1], "user": ["bob"]}).to_csv(path, index=False)

            with self.assertRaises(ValueError):
                load_posts(str(path))

    def test_load_posts_returns_cleaned_dataframe(self) -> None:
        from src.io import load_posts

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "posts.csv"
            pd.DataFrame(
                {
                    "post_id": [1],
                    "user": ["bob"],
                    "timestamp": ["2026-02-02 09:30:00"],
                    "text": ["Visit www.example.com   soon"],
                }
            ).to_csv(path, index=False)

            loaded = load_posts(str(path))
            self.assertEqual(loaded.loc[0, "text_clean"], "Visit soon")


if __name__ == "__main__":
    unittest.main()
