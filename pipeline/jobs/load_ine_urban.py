"""Load INE Indicadores Urbanos (table 69330) for MVP municipalities."""

from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path

from pipeline import DATA_DIR, DB_PATH, connect
from pipeline.jobs.init_db import derive_gross_yield, main as init_db_main
from pipeline.scoring import compute_and_store_scores

INE_PATH = DATA_DIR / "raw" / "ine" / "69330.csv"
INE_URL = "https://www.ine.es/jaxiT3/files/t/es/csv_bdsc/69330.csv"
INE_TABLE = "https://www.ine.es/jaxiT3/Tabla.htm?t=69330"

MUNICIPIO_TO_ADMIN = {
    "Alacant/Alicante": "03014",
    "Málaga": "29067",
    "València": "46250",
}

PROPERTY_METRIC = "Precio medio por metro cuadrado de la vivienda (Euros/m2)"
CRIME_METRIC = "Total infracciones penales (Tasa por mil habitantes)"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def parse_es_number(raw: str | None) -> float | None:
    if raw is None:
        return None
    text = str(raw).strip()
    if not text or text in {".", "..", "..."}:
        return None
    text = text.replace(".", "").replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return None


def ensure_source(conn) -> int:
    row = conn.execute("SELECT id FROM data_source WHERE code = 'ine_urban'").fetchone()
    if row:
        return int(row["id"])
    conn.execute(
        """
        INSERT INTO data_source (code, name, homepage_url, license_note, notes)
        VALUES (
          'ine_urban',
          'INE Indicadores Urbanos',
          ?,
          'Official Spanish statistics — attribute INE',
          'Table 69330 municipalities >20k; notarial purchase prices from 2025 edition'
        )
        """,
        (INE_TABLE,),
    )
    conn.commit()
    return int(
        conn.execute("SELECT id FROM data_source WHERE code = 'ine_urban'").fetchone()["id"]
    )


def ensure_crime_metric(conn) -> int:
    row = conn.execute(
        "SELECT id FROM metric_definition WHERE code = 'crime_rate_per_1000'"
    ).fetchone()
    if row:
        return int(row["id"])
    conn.execute(
        """
        INSERT INTO metric_definition
          (code, name, description, category, unit, higher_is_better, is_derived)
        VALUES (
          'crime_rate_per_1000',
          'Criminal offences rate',
          'Total criminal offences per 1,000 inhabitants (INE Urban Indicators)',
          'safety',
          'per_1000',
          0,
          0
        )
        """
    )
    conn.commit()
    return int(
        conn.execute(
            "SELECT id FROM metric_definition WHERE code = 'crime_rate_per_1000'"
        ).fetchone()["id"]
    )


def ensure_living_crime_weight(conn) -> None:
    living = conn.execute(
        "SELECT id FROM score_definition WHERE code = 'living_score'"
    ).fetchone()
    crime = conn.execute(
        "SELECT id FROM metric_definition WHERE code = 'crime_rate_per_1000'"
    ).fetchone()
    if not living or not crime:
        return
    conn.execute(
        """
        INSERT INTO score_weight (score_definition_id, metric_id, weight)
        VALUES (?, ?, 0.15)
        ON CONFLICT(score_definition_id, metric_id) DO UPDATE SET weight=excluded.weight
        """,
        (int(living["id"]), int(crime["id"])),
    )
    conn.commit()


def read_rows(path: Path) -> list[dict]:
    out: list[dict] = []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            mun = row.get("Municipios")
            if mun not in MUNICIPIO_TO_ADMIN:
                continue
            indicator = row.get("Indicadores") or ""
            if indicator not in {PROPERTY_METRIC, CRIME_METRIC}:
                continue
            value = parse_es_number(row.get("Total"))
            if value is None:
                continue
            period = (row.get("Periodo") or "").strip()
            if not period.isdigit():
                continue
            out.append(
                {
                    "admin_code": MUNICIPIO_TO_ADMIN[mun],
                    "indicator": indicator,
                    "year": int(period),
                    "value": value,
                }
            )
    return out


def upsert(conn, rows: list[dict], source_id: int) -> int:
    metric_ids = {
        row["code"]: int(row["id"])
        for row in conn.execute("SELECT id, code FROM metric_definition").fetchall()
    }
    locations = {
        row["admin_code"]: int(row["id"])
        for row in conn.execute(
            "SELECT id, admin_code FROM location WHERE admin_code IS NOT NULL"
        ).fetchall()
    }
    seed = conn.execute("SELECT id FROM data_source WHERE code = 'seed_manual'").fetchone()
    collected = utc_now_iso()
    count = 0

    # Replace provisional property seed so latest official value wins cleanly.
    if seed and "property_price_m2" in metric_ids:
        for loc_id in locations.values():
            conn.execute(
                """
                DELETE FROM metric_observation
                WHERE location_id = ? AND metric_id = ? AND source_id = ?
                """,
                (loc_id, metric_ids["property_price_m2"], int(seed["id"])),
            )

    for row in rows:
        loc_id = locations.get(row["admin_code"])
        if loc_id is None:
            continue
        if row["indicator"] == PROPERTY_METRIC:
            metric_id = metric_ids["property_price_m2"]
            unit_currency = "EUR"
        else:
            metric_id = metric_ids["crime_rate_per_1000"]
            unit_currency = None
        period = f"{row['year']}-01-01"
        period_end = f"{row['year']}-12-31"
        conn.execute(
            """
            INSERT INTO metric_observation
              (location_id, metric_id, source_id, period_start, period_end, value,
               currency_code, quality_flag, source_url, collected_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'ok', ?, ?)
            ON CONFLICT(location_id, metric_id, period_start, source_id) DO UPDATE SET
              period_end=excluded.period_end,
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
                period_end,
                round(row["value"], 3),
                unit_currency,
                INE_URL,
                collected,
            ),
        )
        count += 1
    conn.commit()
    return count


def main() -> None:
    if not INE_PATH.exists():
        raise FileNotFoundError(f"Missing {INE_PATH}. Download from {INE_URL}")
    if not DB_PATH.exists():
        init_db_main()

    rows = read_rows(INE_PATH)
    print(f"Parsed {len(rows)} INE observation rows for MVP cities")
    for row in rows:
        if row["indicator"] == PROPERTY_METRIC:
            print(
                f"  property {row['admin_code']} {row['year']}: {row['value']} EUR/m2"
            )

    conn = connect()
    source_id = ensure_source(conn)
    ensure_crime_metric(conn)
    ensure_living_crime_weight(conn)
    n = upsert(conn, rows, source_id)
    derive_gross_yield(conn)
    compute_and_store_scores(conn)
    conn.close()
    print(f"Upserted {n} INE observations")


if __name__ == "__main__":
    main()
