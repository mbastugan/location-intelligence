from __future__ import annotations

import sqlite3
from pathlib import Path

from apps.api.db import get_settings


def connect() -> sqlite3.Connection:
    settings = get_settings()
    path = Path(settings.sqlite_path)
    if not path.is_absolute():
        # Resolve relative to repo root (two levels above apps/api)
        root = Path(__file__).resolve().parents[2]
        path = (root / path).resolve()
    if not path.exists():
        raise FileNotFoundError(
            f"Database not found at {path}. Run: python -m pipeline.jobs.init_db"
        )
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn
