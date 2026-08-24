"""Weighted min-max scoring across the current city set."""

from __future__ import annotations

from datetime import datetime, timezone


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _latest_values(conn, metric_id: int) -> dict[int, float]:
    rows = conn.execute(
        """
        SELECT location_id, value
        FROM metric_observation
        WHERE metric_id = ?
          AND period_start = (
            SELECT MAX(period_start)
            FROM metric_observation o2
            WHERE o2.location_id = metric_observation.location_id
              AND o2.metric_id = metric_observation.metric_id
          )
        """,
        (metric_id,),
    ).fetchall()
    return {int(r["location_id"]): float(r["value"]) for r in rows}


def _normalize(values: dict[int, float], higher_is_better: int | None) -> dict[int, float]:
    if not values:
        return {}
    lo = min(values.values())
    hi = max(values.values())
    if hi == lo:
        return {k: 0.5 for k in values}
    out: dict[int, float] = {}
    for loc_id, raw in values.items():
        norm = (raw - lo) / (hi - lo)
        if higher_is_better == 0:
            norm = 1.0 - norm
        out[loc_id] = norm
    return out


def compute_and_store_scores(conn) -> None:
    score_defs = conn.execute("SELECT * FROM score_definition").fetchall()
    locations = [int(r["id"]) for r in conn.execute("SELECT id FROM location").fetchall()]
    collected = utc_now_iso()

    for score_def in score_defs:
        weights = conn.execute(
            """
            SELECT sw.metric_id, sw.weight, md.higher_is_better, md.code
            FROM score_weight sw
            JOIN metric_definition md ON md.id = sw.metric_id
            WHERE sw.score_definition_id = ?
            """,
            (score_def["id"],),
        ).fetchall()

        total_weight = sum(float(w["weight"]) for w in weights) or 1.0
        per_location: dict[int, list[tuple[float, float]]] = {loc: [] for loc in locations}

        for w in weights:
            values = _latest_values(conn, int(w["metric_id"]))
            norms = _normalize(values, w["higher_is_better"])
            for loc_id, norm in norms.items():
                per_location[loc_id].append((norm, float(w["weight"])))

        for loc_id, parts in per_location.items():
            used = sum(weight for _, weight in parts)
            coverage = used / total_weight
            if not parts:
                continue
            score = 100.0 * sum(norm * weight for norm, weight in parts) / used
            quality = "ok" if coverage >= 0.7 else "partial"
            conn.execute(
                """
                INSERT INTO location_score
                  (location_id, score_definition_id, value, coverage, quality_flag, computed_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(location_id, score_definition_id) DO UPDATE SET
                  value=excluded.value,
                  coverage=excluded.coverage,
                  quality_flag=excluded.quality_flag,
                  computed_at=excluded.computed_at
                """,
                (
                    loc_id,
                    score_def["id"],
                    round(score, 1),
                    round(coverage, 3),
                    quality,
                    collected,
                ),
            )
    conn.commit()
