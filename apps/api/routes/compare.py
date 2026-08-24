from __future__ import annotations

from fastapi import APIRouter, HTTPException

from apps.api.database import connect
from apps.api.services import build_city_payload, build_compare

router = APIRouter(prefix="/compare", tags=["compare"])


@router.get("/{pair}")
def compare_cities(pair: str) -> dict:
    """pair format: malaga-vs-alicante"""
    if "-vs-" not in pair:
        raise HTTPException(status_code=400, detail="Use slug-vs-slug, e.g. malaga-vs-alicante")
    left, right = pair.split("-vs-", 1)
    if not left or not right:
        raise HTTPException(status_code=400, detail="Both city slugs are required")

    conn = connect()
    try:
        a = build_city_payload(conn, left)
        b = build_city_payload(conn, right)
        if a is None or b is None:
            missing = left if a is None else right
            raise HTTPException(status_code=404, detail=f"City not found: {missing}")
        return build_compare(a, b)
    finally:
        conn.close()
