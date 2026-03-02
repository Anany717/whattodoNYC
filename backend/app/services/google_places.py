from __future__ import annotations

from typing import Any

import requests
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Place, PlaceSource, PlaceType

GOOGLE_TEXT_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"


def fetch_and_cache_google_places(
    db: Session,
    *,
    query: str,
    lat: float,
    lng: float,
    radius_km: float,
    limit: int = 15,
) -> list[Place]:
    if not settings.google_places_api_key:
        return []

    params = {
        "query": query,
        "location": f"{lat},{lng}",
        "radius": int(radius_km * 1000),
        "key": settings.google_places_api_key,
    }
    try:
        response = requests.get(GOOGLE_TEXT_SEARCH_URL, params=params, timeout=8)
        response.raise_for_status()
        payload: dict[str, Any] = response.json()
    except Exception:
        return []

    results = payload.get("results", [])[:limit]
    cached: list[Place] = []
    for item in results:
        place_id = item.get("place_id")
        if not place_id:
            continue
        existing = db.scalar(select(Place).where(Place.google_place_id == place_id))
        if existing:
            cached.append(existing)
            continue

        geometry = (item.get("geometry") or {}).get("location") or {}
        place_type = PlaceType.restaurant
        types = item.get("types") or []
        if "tourist_attraction" in types or "park" in types:
            place_type = PlaceType.activity
        if "event" in types:
            place_type = PlaceType.event

        record = Place(
            google_place_id=place_id,
            source=PlaceSource.google,
            place_type=place_type,
            name=item.get("name", "Unknown Place"),
            formatted_address=item.get("formatted_address"),
            neighborhood=None,
            lat=geometry.get("lat", lat),
            lng=geometry.get("lng", lng),
            price_level=item.get("price_level"),
            phone=None,
            website=None,
        )
        db.add(record)
        db.flush()
        cached.append(record)

    db.commit()
    return cached
