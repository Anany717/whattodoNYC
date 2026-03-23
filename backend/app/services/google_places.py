from __future__ import annotations

import logging
from typing import Any

import requests
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Place, PlaceSource, PlaceTag, PlaceType, Tag
from app.utils.geo import haversine_km

GOOGLE_TEXT_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
NYC_HINTS = ("new york", "nyc", "manhattan", "brooklyn", "queens", "bronx", "staten island")
logger = logging.getLogger(__name__)


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
        "query": _query_with_city_hint(query),
        "location": f"{lat},{lng}",
        "radius": min(50000, max(500, int(radius_km * 1000))),
        "region": "us",
        "key": settings.google_places_api_key,
    }

    try:
        response = requests.get(GOOGLE_TEXT_SEARCH_URL, params=params, timeout=8)
        response.raise_for_status()
        payload: dict[str, Any] = response.json()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Google Places request failed: %s", exc)
        return []

    status = payload.get("status", "UNKNOWN")
    if status == "ZERO_RESULTS":
        return []
    if status != "OK":
        logger.warning("Google Places returned status %s for query %r", status, query)
        return []

    cached: list[Place] = []
    for item in (payload.get("results") or [])[:limit]:
        normalized = _normalize_google_result(item, fallback_lat=lat, fallback_lng=lng)
        if not normalized:
            continue

        place = _upsert_google_place(db, normalized)
        if place is not None:
            cached.append(place)

    db.commit()
    return cached


def _query_with_city_hint(query: str) -> str:
    normalized = query.lower()
    if any(hint in normalized for hint in NYC_HINTS):
        return query
    return f"{query} NYC"


def _normalize_google_result(
    item: dict[str, Any],
    *,
    fallback_lat: float,
    fallback_lng: float,
) -> dict[str, Any] | None:
    google_place_id = item.get("place_id")
    name = item.get("name")
    if not google_place_id or not name:
        return None

    geometry = (item.get("geometry") or {}).get("location") or {}
    types = [value for value in item.get("types") or [] if isinstance(value, str)]
    formatted_address = item.get("formatted_address") or item.get("vicinity")
    lat = geometry.get("lat", fallback_lat)
    lng = geometry.get("lng", fallback_lng)
    price_level = item.get("price_level")

    return {
        "google_place_id": google_place_id,
        "name": name,
        "formatted_address": formatted_address,
        "neighborhood": _extract_neighborhood(formatted_address),
        "lat": lat,
        "lng": lng,
        "price_level": (
            price_level if isinstance(price_level, int) and 1 <= price_level <= 4 else None
        ),
        "place_type": _map_place_type(types),
        "tags": _google_tags(types),
    }


def _map_place_type(types: list[str]) -> PlaceType:
    lowered = set(types)
    if lowered & {"event_venue", "concert_hall", "movie_theater", "night_club"}:
        return PlaceType.event
    if lowered & {
        "tourist_attraction",
        "park",
        "museum",
        "art_gallery",
        "amusement_park",
        "stadium",
        "campground",
        "gym",
        "spa",
        "bowling_alley",
    }:
        return PlaceType.activity
    return PlaceType.restaurant


def _google_tags(types: list[str]) -> list[str]:
    skip = {
        "point_of_interest",
        "establishment",
        "food",
        "store",
        "premise",
    }
    tags: list[str] = []
    for place_type in types:
        if place_type in skip:
            continue
        tags.append(place_type.replace("_", "-"))
    return tags[:6]


def _extract_neighborhood(address: str | None) -> str | None:
    if not address:
        return None
    parts = [part.strip() for part in address.split(",") if part.strip()]
    if len(parts) >= 2:
        return parts[-3] if len(parts) >= 3 else parts[0]
    return parts[0] if parts else None


def _upsert_google_place(db: Session, payload: dict[str, Any]) -> Place | None:
    existing = db.scalar(select(Place).where(Place.google_place_id == payload["google_place_id"]))
    if not existing:
        existing = _find_similar_place(db, payload)

    if existing:
        if not existing.google_place_id:
            existing.google_place_id = payload["google_place_id"]
        if existing.source != PlaceSource.internal:
            existing.source = PlaceSource.google
        if payload.get("formatted_address") and not existing.formatted_address:
            existing.formatted_address = payload["formatted_address"]
        if payload.get("neighborhood") and not existing.neighborhood:
            existing.neighborhood = payload["neighborhood"]
        if payload.get("price_level") and existing.price_level is None:
            existing.price_level = payload["price_level"]
        if existing.source == PlaceSource.google:
            existing.lat = payload["lat"]
            existing.lng = payload["lng"]
            existing.place_type = payload["place_type"]
        _sync_tags(db, existing, payload["tags"])
        db.add(existing)
        db.flush()
        return existing

    place = Place(
        google_place_id=payload["google_place_id"],
        source=PlaceSource.google,
        place_type=payload["place_type"],
        name=payload["name"],
        formatted_address=payload["formatted_address"],
        neighborhood=payload["neighborhood"],
        lat=payload["lat"],
        lng=payload["lng"],
        price_level=payload["price_level"],
        phone=None,
        website=None,
    )
    db.add(place)
    db.flush()
    _sync_tags(db, place, payload["tags"])
    return place


def _find_similar_place(db: Session, payload: dict[str, Any]) -> Place | None:
    candidates = list(db.scalars(select(Place).where(Place.name.ilike(payload["name"]))).all())
    normalized_name = _normalize_text(payload["name"])
    normalized_address = _normalize_text(payload.get("formatted_address"))

    for candidate in candidates:
        if _normalize_text(candidate.name) != normalized_name:
            continue
        candidate_address = _normalize_text(candidate.formatted_address)
        if candidate_address and normalized_address and candidate_address == normalized_address:
            return candidate
        if haversine_km(candidate.lat, candidate.lng, payload["lat"], payload["lng"]) <= 0.15:
            return candidate
    return None


def _sync_tags(db: Session, place: Place, names: list[str]) -> None:
    existing_names = {place_tag.tag.name.lower() for place_tag in place.tags if place_tag.tag}
    for raw_name in names:
        name = raw_name.strip().lower()
        if not name or name in existing_names:
            continue
        tag = db.scalar(select(Tag).where(Tag.name == name))
        if not tag:
            tag = Tag(name=name)
            db.add(tag)
            db.flush()
        db.add(PlaceTag(place_id=place.id, tag_id=tag.id))
        existing_names.add(name)


def _normalize_text(value: str | None) -> str:
    return " ".join((value or "").lower().replace("'", "").split())
