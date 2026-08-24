from __future__ import annotations

from fastapi import APIRouter, HTTPException

from apps.api.database import connect
from apps.api.services import build_city_payload, list_cities

router = APIRouter(prefix="/cities", tags=["cities"])


@router.get("")
def get_cities() -> list[dict]:
    conn = connect()
    try:
        return list_cities(conn)
    finally:
        conn.close()


@router.get("/{slug}")
def get_city(slug: str) -> dict:
    conn = connect()
    try:
        payload = build_city_payload(conn, slug)
        if payload is None:
            raise HTTPException(status_code=404, detail=f"City not found: {slug}")
        return payload
    finally:
        conn.close()
