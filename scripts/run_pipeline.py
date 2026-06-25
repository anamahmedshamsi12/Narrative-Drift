"""
Run the Narrative Drift pipeline.

Usage (from project root):
  python3 scripts/run_pipeline.py --input data/sample_posts.csv
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# --- Fix imports so `from src...` works when running as a script ---
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline import run_pipeline  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Narrative Drift pipeline.")
    parser.add_argument(
        "--input",
        required=True,
        help="Path to input CSV (must include columns like text and timestamp; user/post_id recommended).",
    )
    parser.add_argument(
        "--artifacts",
        default="artifacts",
        help="Artifacts output directory (default: artifacts).",
    )
    parser.add_argument(
        "--model",
        default="sentence-transformers/all-MiniLM-L6-v2",
        help="SentenceTransformer model name (default: sentence-transformers/all-MiniLM-L6-v2).",
    )
    parser.add_argument(
        "--clusters",
        type=int,
        default=8,
        help="Number of clusters (default: 8).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        raise FileNotFoundError(
            f"Input CSV not found: {input_path}\n"
            f"Run from the project root and use something like:\n"
            f"  python3 scripts/run_pipeline.py --input data/sample_posts.csv"
        )

    artifacts_dir = Path(args.artifacts)
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    run_pipeline(
        input_csv=str(input_path),
        artifacts_dir=str(artifacts_dir),
        model_name=args.model,
        n_clusters=args.clusters,
    )


if __name__ == "__main__":
    main()