"""Create SQLite DB, load seed observations, compute derived metrics + scores."""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path

from pipeline import DB_PATH, ROOT, apply_schema, connect
from pipeline.scoring import compute_and_store_scores

SEED_PATH = ROOT / "pipeline" / "seeds" / "mvp_seed.json"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_seed(conn, seed: dict) -> None:
    for country in seed["countries"]:
        conn.execute(
            """
            INSERT INTO country (id, iso2, name, currency_code)
            VALUES (:id, :iso2, :name, :currency_code)
            ON CONFLICT(id) DO UPDATE SET
              iso2=excluded.iso2,
              name=excluded.name,
              currency_code=excluded.currency_code
            """,
            country,
        )

    for source in seed["data_sources"]:
        conn.execute(
            """
            INSERT INTO data_source (id, code, name, homepage_url, license_note, notes)
            VALUES (:id, :code, :name, :homepage_url, :license_note, :notes)
            ON CONFLICT(id) DO UPDATE SET
              code=excluded.code,
              name=excluded.name,
              homepage_url=excluded.homepage_url,
              license_note=excluded.license_note,
              notes=excluded.notes
            """,
            source,
        )

    for metric in seed["metrics"]:
        hib = metric.get("higher_is_better")
        hib_int = None if hib is None else (1 if hib else 0)
        conn.execute(
            """
            INSERT INTO metric_definition
              (id, code, name, description, category, unit, higher_is_better, is_derived)
            VALUES
              (:id, :code, :name, :description, :category, :unit, :higher_is_better, :is_derived)
            ON CONFLICT(id) DO UPDATE SET
              code=excluded.code,
              name=excluded.name,
              description=excluded.description,
              category=excluded.category,
              unit=excluded.unit,
              higher_is_better=excluded.higher_is_better,
              is_derived=excluded.is_derived
            """,
            {
                **metric,
                "higher_is_better": hib_int,
                "is_derived": 1 if metric.get("is_derived") else 0,
            },
        )

    for loc in seed["locations"]:
        conn.execute(
            """
            INSERT INTO location
              (id, country_id, slug, name, name_local, admin_code, location_type, lat, lon)
            VALUES
              (:id, :country_id, :slug, :name, :name_local, :admin_code, :location_type, :lat, :lon)
            ON CONFLICT(id) DO UPDATE SET
              country_id=excluded.country_id,
              slug=excluded.slug,
              name=excluded.name,
              name_local=excluded.name_local,
              admin_code=excluded.admin_code,
              location_type=excluded.location_type,
              lat=excluded.lat,
              lon=excluded.lon
            """,
            loc,
        )

    for obs in seed["observations"]:
        conn.execute(
            """
            INSERT INTO metric_observation
              (location_id, metric_id, source_id, period_start, period_end, value,
               currency_code, quality_flag, source_url, collected_at)
            VALUES
              (:location_id, :metric_id, :source_id, :period_start, :period_end, :value,
               :currency_code, :quality_flag, :source_url, :collected_at)
            ON CONFLICT(location_id, metric_id, period_start, source_id) DO UPDATE SET
              period_end=excluded.period_end,
              value=excluded.value,
              currency_code=excluded.currency_code,
              quality_flag=excluded.quality_flag,
              source_url=excluded.source_url,
              collected_at=excluded.collected_at
            """,
            {
                **obs,
                "collected_at": obs.get("collected_at") or utc_now_iso(),
            },
        )

    for score_def in seed["score_definitions"]:
        conn.execute(
            """
            INSERT INTO score_definition (id, code, name, version, description)
            VALUES (:id, :code, :name, :version, :description)
            ON CONFLICT(id) DO UPDATE SET
              code=excluded.code,
              name=excluded.name,
              version=excluded.version,
              description=excluded.description
            """,
            score_def,
        )

    for weight in seed["score_weights"]:
        conn.execute(
            """
            INSERT INTO score_weight (score_definition_id, metric_id, weight)
            VALUES (:score_definition_id, :metric_id, :weight)
            ON CONFLICT(score_definition_id, metric_id) DO UPDATE SET
              weight=excluded.weight
            """,
            weight,
        )

    conn.commit()


def derive_gross_yield(conn) -> None:
    """estimated_gross_yield = rent_m2 * 12 / property_price_m2 * 100."""
    metric_ids = {
        row["code"]: row["id"]
        for row in conn.execute("SELECT id, code FROM metric_definition").fetchall()
    }
    source_id = conn.execute(
        "SELECT id FROM data_source WHERE code = 'derived_internal'"
    ).fetchone()["id"]
    price_id = metric_ids["property_price_m2"]
    rent_id = metric_ids["rent_m2"]
    yield_id = metric_ids["estimated_gross_yield"]
    collected = utc_now_iso()

    rows = conn.execute(
        """
        SELECT p.location_id, p.period_start, p.value AS price, r.value AS rent
        FROM metric_observation p
        JOIN metric_observation r
          ON r.location_id = p.location_id
         AND r.period_start = p.period_start
         AND r.metric_id = ?
        WHERE p.metric_id = ?
        """,
        (rent_id, price_id),
    ).fetchall()

    for row in rows:
        if not row["price"]:
            continue
        value = (row["rent"] * 12.0 / row["price"]) * 100.0
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
                row["location_id"],
                yield_id,
                source_id,
                row["period_start"],
                row["period_start"],
                round(value, 2),
                collected,
            ),
        )
    conn.commit()


def main() -> None:
    seed = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    if DB_PATH.exists():
        DB_PATH.unlink()
    conn = connect()
    apply_schema(conn)
    load_seed(conn, seed)
    derive_gross_yield(conn)
    compute_and_store_scores(conn)
    conn.close()
    print(f"Initialized database at {DB_PATH}")
    print(f"Seed collected_at reference date: {date.today().isoformat()}")


if __name__ == "__main__":
    main()
