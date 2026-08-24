"""Load official municipal population from INE Padrón table 29005."""

from __future__ import annotations

import csv
import re
from datetime import datetime, timezone
from pathlib import Path

from pipeline import DATA_DIR, DB_PATH, connect
from pipeline.jobs.init_db import main as init_db_main
from pipeline.scoring import compute_and_store_scores

PADRON_PATH = DATA_DIR / "raw" / "ine" / "29005.csv"
PADRON_URL = "https://www.ine.es/jaxiT3/files/t/es/csv_bdsc/29005.csv"
PADRON_TABLE = "https://www.ine.es/jaxiT3/Tabla.htm?t=29005"

TARGET_CODES = {"03014", "29067", "46250"}
CODE_RE = re.compile(r"^(\d{5})\s+")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def parse_es_number(raw: str | None) -> float | None:
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    text = text.replace(".", "").replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return None


def ensure_source(conn) -> int:
    row = conn.execute("SELECT id FROM data_source WHERE code = 'ine_padron'").fetchone()
    if row:
        return int(row["id"])
    conn.execute(
        """
        INSERT INTO data_source (code, name, homepage_url, license_note, notes)
        VALUES (
          'ine_padron',
          'INE Padrón municipal',
          ?,
          'Official Spanish statistics — attribute INE',
          'Official municipal population figures (table 29005)'
        )
        """,
        (PADRON_TABLE,),
    )
    conn.commit()
    return int(
        conn.execute("SELECT id FROM data_source WHERE code = 'ine_padron'").fetchone()["id"]
    )


def read_population(path: Path) -> list[dict]:
    out: list[dict] = []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=";")
        for row in reader:
            if (row.get("Sexo") or "").strip() != "Total":
                continue
            mun = row.get("Municipios") or ""
            match = CODE_RE.match(mun)
            if not match:
                continue
            code = match.group(1)
            if code not in TARGET_CODES:
                continue
            year = (row.get("Periodo") or "").strip()
            if not year.isdigit():
                continue
            value = parse_es_number(row.get("Total"))
            if value is None:
                continue
            out.append({"admin_code": code, "year": int(year), "value": value})
    return out


def upsert(conn, rows: list[dict], source_id: int) -> int:
    metric_id = int(
        conn.execute(
            "SELECT id FROM metric_definition WHERE code = 'population'"
        ).fetchone()["id"]
    )
    locations = {
        row["admin_code"]: int(row["id"])
        for row in conn.execute(
            "SELECT id, admin_code FROM location WHERE admin_code IS NOT NULL"
        ).fetchall()
    }
    seed = conn.execute("SELECT id FROM data_source WHERE code = 'seed_manual'").fetchone()
    collected = utc_now_iso()
    count = 0

    if seed:
        for loc_id in locations.values():
            conn.execute(
                """
                DELETE FROM metric_observation
                WHERE location_id = ? AND metric_id = ? AND source_id = ?
                """,
                (loc_id, metric_id, int(seed["id"])),
            )

    for row in rows:
        loc_id = locations.get(row["admin_code"])
        if loc_id is None:
            continue
        period = f"{row['year']}-01-01"
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
                loc_id,
                metric_id,
                source_id,
                period,
                period,
                row["value"],
                PADRON_URL,
                collected,
            ),
        )
        count += 1
    conn.commit()
    return count


def derive_population_growth(conn) -> int:
    """population_growth_1y = (pop_t - pop_t-1) / pop_t-1 * 100."""
    metric_ids = {
        row["code"]: int(row["id"])
        for row in conn.execute("SELECT id, code FROM metric_definition").fetchall()
    }
    if "population_growth_1y" not in metric_ids:
        conn.execute(
            """
            INSERT INTO metric_definition
              (code, name, description, category, unit, higher_is_better, is_derived)
            VALUES (
              'population_growth_1y',
              'Population growth (1 year)',
              '(pop_t - pop_t-1) / pop_t-1 * 100',
              'population',
              '%',
              1,
              1
            )
            """
        )
        conn.commit()
        metric_ids["population_growth_1y"] = int(
            conn.execute(
                "SELECT id FROM metric_definition WHERE code = 'population_growth_1y'"
            ).fetchone()["id"]
        )

    source_id = int(
        conn.execute("SELECT id FROM data_source WHERE code = 'derived_internal'").fetchone()[
            "id"
        ]
    )
    pop_id = metric_ids["population"]
    growth_id = metric_ids["population_growth_1y"]
    collected = utc_now_iso()
    count = 0

    locations = conn.execute("SELECT id FROM location").fetchall()
    for loc in locations:
        rows = conn.execute(
            """
            SELECT period_start, value
            FROM metric_observation
            WHERE location_id = ? AND metric_id = ?
            ORDER BY period_start
            """,
            (int(loc["id"]), pop_id),
        ).fetchall()
        by_year = {int(r["period_start"][:4]): float(r["value"]) for r in rows}
        for year, value in by_year.items():
            prev = by_year.get(year - 1)
            if prev is None or prev == 0:
                continue
            growth = (value - prev) / prev * 100.0
            period = f"{year}-01-01"
            conn.execute(
                """
                INSERT INTO metric_observation
                  (location_id, metric_id, source_id, period_start, period_end, value,
                   currency_code, quality_flag, source_url, collected_at)
                VALUES (?, ?, ?, ?, ?, ?, NULL, 'estimated', NULL, ?)
                ON CONFLICT(location_id, metric_id, period_start, source_id) DO UPDATE SET
                  value=excluded.value,
                  quality_flag=excluded.quality_flag,
                  collected_at=excluded.collected_at
                """,
                (
                    int(loc["id"]),
                    growth_id,
                    source_id,
                    period,
                    period,
                    round(growth, 3),
                    collected,
                ),
            )
            count += 1
    conn.commit()
    return count


def main() -> None:
    if not PADRON_PATH.exists():
        raise FileNotFoundError(f"Missing {PADRON_PATH}. Download from {PADRON_URL}")
    if not DB_PATH.exists():
        init_db_main()

    rows = read_population(PADRON_PATH)
    latest = {}
    for row in rows:
        latest[row["admin_code"]] = row
    for code, row in sorted(latest.items()):
        print(f"{code} {row['year']}: {row['value']:,.0f}")

    conn = connect()
    source_id = ensure_source(conn)
    n = upsert(conn, rows, source_id)
    g = derive_population_growth(conn)
    compute_and_store_scores(conn)
    conn.close()
    print(f"Upserted {n} population rows, {g} growth rows")


if __name__ == "__main__":
    main()
