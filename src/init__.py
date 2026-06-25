"""
Narrative Drift package.

Public API re-exports live here to keep imports clean.
"""

from __future__ import annotations

__all__ = [
    "run_pipeline",
    "PipelineConfig",
]

__version__ = "0.1.0"

from .pipeline import PipelineConfig, run_pipeline
