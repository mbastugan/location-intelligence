"""Load annual mean temperature from Open-Meteo archive (no API key).

AEMET is preferred long-term; this fills climate with a free, legal source until
an AEMET API key is configured.
"""

from __future__ import annotations

from datetime import datetime, timezone

import httpx

from pipeline import DB_PATH, connect
from pipeline.jobs.init_db import main as init_db_main
from pipeline.scoring import compute_and_store_scores

ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def ensure_source(conn) -> int:
    row = conn.execute(
        "SELECT id FROM data_source WHERE code = 'open_meteo'"
    ).fetchone()
    if row:
        return int(row["id"])
    conn.execute(
        """
        INSERT INTO data_source (code, name, homepage_url, license_note, notes)
        VALUES (
          'open_meteo',
          'Open-Meteo Archive',
          'https://open-meteo.com/',
          'CC BY 4.0 — attribute Open-Meteo',
          'Interim climate source until AEMET OpenData key is configured'
        )
        """
    )
    conn.commit()
    return int(
        conn.execute(
            "SELECT id FROM data_source WHERE code = 'open_meteo'"
        ).fetchone()["id"]
    )


def fetch_annual_mean(lat: float, lon: float, year: int) -> float:
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": f"{year}-01-01",
        "end_date": f"{year}-12-31",
        "daily": "temperature_2m_mean",
        "timezone": "Europe/Madrid",
    }
    with httpx.Client(timeout=60.0) as client:
        response = client.get(ARCHIVE_URL, params=params)
        response.raise_for_status()
        payload = response.json()
    values = payload["daily"]["temperature_2m_mean"]
    clean = [v for v in values if v is not None]
    if not clean:
        raise RuntimeError(f"No temperature values for {lat},{lon} {year}")
    return sum(clean) / len(clean)


def main() -> None:
    if not DB_PATH.exists():
        init_db_main()

    conn = connect()
    source_id = ensure_source(conn)
    metric_id = int(
        conn.execute(
            "SELECT id FROM metric_definition WHERE code = 'avg_temp_annual'"
        ).fetchone()["id"]
    )
    seed = conn.execute("SELECT id FROM data_source WHERE code = 'seed_manual'").fetchone()
    locations = conn.execute(
        "SELECT id, slug, lat, lon FROM location WHERE lat IS NOT NULL"
    ).fetchall()
    collected = utc_now_iso()
    year = 2024

    for loc in locations:
        mean_temp = fetch_annual_mean(float(loc["lat"]), float(loc["lon"]), year)
        print(f"{loc['slug']}: {mean_temp:.2f} C ({year})")
        if seed:
            conn.execute(
                """
                DELETE FROM metric_observation
                WHERE location_id = ? AND metric_id = ? AND source_id = ?
                """,
                (int(loc["id"]), metric_id, int(seed["id"])),
            )
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
                f"{year}-12-31",
                round(mean_temp, 2),
                ARCHIVE_URL,
                collected,
            ),
        )
    conn.commit()
    compute_and_store_scores(conn)
    conn.close()
    print("Open-Meteo climate load complete")


if __name__ == "__main__":
    main()
