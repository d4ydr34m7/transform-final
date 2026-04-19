"""Paths and AWS region for the backend."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent / "analysis_outputs"
DB_PATH = Path(__file__).parent / "analysis_runs.sqlite3"


def get_region() -> str | None:
    region = os.environ.get("AWS_REGION", "").strip() or os.environ.get("AWS_DEFAULT_REGION", "").strip()
    return region or None
