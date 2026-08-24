"""Compute nearest large-airport distance from OurAirports open data."""

from __future__ import annotations

import csv
import math
from datetime import datetime, timezone
from pathlib import Path

from pipeline import DATA_DIR, DB_PATH, connect
from pipeline.jobs.init_db import main as init_db_main
from pipeline.scoring import compute_and_store_scores

AIRPORTS_PATH = DATA_DIR / "raw" / "airports" / "airports.csv"
AIRPORTS_URL = "https://davidmegginson.github.io/ourairports-data/airports.csv"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def ensure_source(conn) -> int:
    row = conn.execute("SELECT id FROM data_source WHERE code = 'ourairports'").fetchone()
    if row:
        return int(row["id"])
    conn.execute(
        """
        INSERT INTO data_source (code, name, homepage_url, license_note, notes)
        VALUES (
          'ourairports',
          'OurAirports',
          'https://ourairports.com/data/',
          'Open data; attribution appreciated',
          'Airport coordinates for nearest-airport distance'
        )
        """
    )
    conn.commit()
    return int(
        conn.execute("SELECT id FROM data_source WHERE code = 'ourairports'").fetchone()["id"]
    )


def load_spain_large_airports(path: Path) -> list[dict]:
    airports: list[dict] = []
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if row.get("iso_country") != "ES":
                continue
            if row.get("type") not in {"large_airport", "medium_airport"}:
                continue
            if (row.get("scheduled_service") or "").lower() != "yes":
                continue
            try:
                lat = float(row["latitude_deg"])
                lon = float(row["longitude_deg"])
            except (KeyError, TypeError, ValueError):
                continue
            airports.append(
                {
                    "ident": row.get("ident") or row.get("gps_code") or "",
                    "name": row.get("name") or "",
                    "iata": row.get("iata_code") or "",
                    "type": row.get("type"),
                    "lat": lat,
                    "lon": lon,
                }
            )
    return airports


def main() -> None:
    if not AIRPORTS_PATH.exists():
        raise FileNotFoundError(f"Missing {AIRPORTS_PATH}. Download from {AIRPORTS_URL}")
    if not DB_PATH.exists():
        init_db_main()

    airports = load_spain_large_airports(AIRPORTS_PATH)
    # Prefer large airports when available within a reasonable radius.
    large = [a for a in airports if a["type"] == "large_airport"]
    pool = large or airports
    print(f"Using {len(pool)} Spanish airports with scheduled service")

    conn = connect()
    source_id = ensure_source(conn)
    metric_id = int(
        conn.execute(
            "SELECT id FROM metric_definition WHERE code = 'airport_distance_km'"
        ).fetchone()["id"]
    )
    collected = utc_now_iso()
    year = datetime.now(timezone.utc).year

    for loc in conn.execute(
        "SELECT id, slug, lat, lon FROM location WHERE lat IS NOT NULL"
    ).fetchall():
        best = None
        best_km = None
        for airport in pool:
            km = haversine_km(
                float(loc["lat"]), float(loc["lon"]), airport["lat"], airport["lon"]
            )
            if best_km is None or km < best_km:
                best_km = km
                best = airport
        assert best is not None and best_km is not None
        label = best["iata"] or best["ident"]
        print(f"{loc['slug']}: {best_km:.1f} km -> {best['name']} ({label})")
        conn.execute(
            """
            INSERT INTO metric_observation
              (location_id, metric_id, source_id, period_start, period_end, value,
               currency_code, quality_flag, source_url, collected_at)
            VALUES (?, ?, ?, ?, ?, ?, NULL, 'ok', ?, ?)
            ON CONFLICT(location_id, metric_id, period_start, source_id) DO UPDATE SET
              value=excluded.value,
              quality_flag=excluded.quality_flag,
              source_url=excluded.source_url,
              collected_at=excluded.collected_at
            """,
            (
                int(loc["id"]),
                metric_id,
                source_id,
                f"{year}-01-01",
                f"{year}-01-01",
                round(best_km, 2),
                AIRPORTS_URL,
                collected,
            ),
        )
    conn.commit()
    compute_and_store_scores(conn)
    conn.close()
    print("Airport distances updated")


if __name__ == "__main__":
    main()
