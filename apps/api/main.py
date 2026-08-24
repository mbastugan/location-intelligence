from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.api.db import get_settings
from apps.api.routes import cities, compare, health

settings = get_settings()

app = FastAPI(
    title="Location Intelligence API",
    version="0.1.0",
    description="MVP API for Spain city metrics and comparisons",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(cities.router)
app.include_router(compare.router)
