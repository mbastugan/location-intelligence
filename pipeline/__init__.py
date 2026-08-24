"""Shared paths and SQLite helpers."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DB_PATH = Path(os.environ.get("LOCATION_DB_PATH", DATA_DIR / "location.db"))
SCHEMA_PATH = ROOT / "db" / "schema.sql"
EXPORT_DIR = DATA_DIR / "exports"
WEB_PUBLIC_DATA = ROOT / "apps" / "web" / "public" / "data"


def connect(db_path: Path | None = None) -> sqlite3.Connection:
    path = db_path or DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def apply_schema(conn: sqlite3.Connection) -> None:
    sql = SCHEMA_PATH.read_text(encoding="utf-8")
    conn.executescript(sql)
    conn.commit()
