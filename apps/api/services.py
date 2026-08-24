from __future__ import annotations


def list_cities(conn) -> list[dict]:
    rows = conn.execute(
        """
        SELECT l.slug, l.name, l.name_local, c.iso2 AS country_iso2, c.name AS country_name
        FROM location l
        JOIN country c ON c.id = l.country_id
        ORDER BY l.name
        """
    ).fetchall()
    return [
        {
            "slug": r["slug"],
            "name": r["name"],
            "name_local": r["name_local"],
            "country": {"iso2": r["country_iso2"], "name": r["country_name"]},
            "path": f"/spain/{r['slug']}",
        }
        for r in rows
    ]


def _city_row(conn, slug: str):
    return conn.execute(
        """
        SELECT l.*, c.iso2 AS country_iso2, c.name AS country_name
        FROM location l
        JOIN country c ON c.id = l.country_id
        WHERE l.slug = ?
        """,
        (slug,),
    ).fetchone()


def _latest_metrics(conn, location_id: int) -> list[dict]:
    rows = conn.execute(
        """
        SELECT md.code, md.name, md.unit, md.category, o.value, o.period_start,
               o.quality_flag, ds.code AS source_code, o.source_url, o.collected_at
        FROM metric_observation o
        JOIN metric_definition md ON md.id = o.metric_id
        JOIN data_source ds ON ds.id = o.source_id
        WHERE o.location_id = ?
          AND o.period_start = (
            SELECT MAX(period_start) FROM metric_observation o2
            WHERE o2.location_id = o.location_id AND o2.metric_id = o.metric_id
          )
        ORDER BY md.category, md.code
        """,
        (location_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def _series(conn, location_id: int, metric_code: str) -> list[dict]:
    rows = conn.execute(
        """
        SELECT o.period_start, o.value, o.quality_flag
        FROM metric_observation o
        JOIN metric_definition md ON md.id = o.metric_id
        WHERE o.location_id = ? AND md.code = ?
        ORDER BY o.period_start
        """,
        (location_id, metric_code),
    ).fetchall()
    return [dict(r) for r in rows]


def _scores(conn, location_id: int) -> list[dict]:
    rows = conn.execute(
        """
        SELECT sd.code, sd.name, sd.version, ls.value, ls.coverage, ls.quality_flag, ls.computed_at
        FROM location_score ls
        JOIN score_definition sd ON sd.id = ls.score_definition_id
        WHERE ls.location_id = ?
        """,
        (location_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def build_city_payload(conn, slug: str) -> dict | None:
    city = _city_row(conn, slug)
    if city is None:
        return None
    return {
        "slug": city["slug"],
        "name": city["name"],
        "name_local": city["name_local"],
        "country": {"iso2": city["country_iso2"], "name": city["country_name"]},
        "admin_code": city["admin_code"],
        "coordinates": {"lat": city["lat"], "lon": city["lon"]},
        "metrics": _latest_metrics(conn, city["id"]),
        "series": {
            "property_price_m2": _series(conn, city["id"], "property_price_m2"),
            "rent_m2": _series(conn, city["id"], "rent_m2"),
            "population": _series(conn, city["id"], "population"),
        },
        "scores": _scores(conn, city["id"]),
    }


def insight_for(
    metric_code: str, left: float, right: float, left_name: str, right_name: str
) -> str | None:
    rules: dict[str, tuple[str, bool]] = {
        "property_price_m2": ("more affordable purchase price", False),
        "rent_m2": ("more affordable rent", False),
        "estimated_gross_yield": ("higher estimated gross yield", True),
        "avg_temp_annual": ("warmer annual climate", True),
        "sunshine_hours_annual": ("more sunshine", True),
        "airport_distance_km": ("closer to a major airport", False),
        "living_score": ("higher living score", True),
        "investment_score": ("higher investment score", True),
    }
    if metric_code not in rules:
        return None
    label, higher = rules[metric_code]
    if left == right:
        return f"Similar on {label}"
    winner = left_name if ((left > right) if higher else (left < right)) else right_name
    return f"{winner}: {label}"


def build_compare(a: dict, b: dict) -> dict:
    metrics_a = {m["code"]: m for m in a["metrics"]}
    metrics_b = {m["code"]: m for m in b["metrics"]}
    codes = sorted(set(metrics_a) | set(metrics_b))
    rows: list[dict] = []
    insights: list[str] = []
    for code in codes:
        ma = metrics_a.get(code)
        mb = metrics_b.get(code)
        rows.append(
            {
                "code": code,
                "name": (ma or mb)["name"],
                "unit": (ma or mb)["unit"],
                "a": None if ma is None else ma["value"],
                "b": None if mb is None else mb["value"],
            }
        )
        if ma is not None and mb is not None:
            tip = insight_for(code, ma["value"], mb["value"], a["name"], b["name"])
            if tip:
                insights.append(tip)

    scores_a = {s["code"]: s for s in a["scores"]}
    scores_b = {s["code"]: s for s in b["scores"]}
    for code in sorted(set(scores_a) | set(scores_b)):
        sa = scores_a.get(code)
        sb = scores_b.get(code)
        rows.append(
            {
                "code": code,
                "name": (sa or sb)["name"],
                "unit": "score_0_100",
                "a": None if sa is None else sa["value"],
                "b": None if sb is None else sb["value"],
            }
        )
        if sa is not None and sb is not None:
            tip = insight_for(code, sa["value"], sb["value"], a["name"], b["name"])
            if tip:
                insights.append(tip)

    return {
        "a": {"slug": a["slug"], "name": a["name"]},
        "b": {"slug": b["slug"], "name": b["name"]},
        "rows": rows,
        "insights": insights,
    }
