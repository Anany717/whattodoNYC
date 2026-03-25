from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import requests
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Place, PlaceSource, PlaceTag, PlaceType, Tag
from app.utils.geo import haversine_km

GOOGLE_TEXT_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
GOOGLE_DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"
DETAIL_FIELDS = ",".join(
    [
        "place_id",
        "name",
        "formatted_address",
        "geometry/location",
        "price_level",
        "formatted_phone_number",
        "website",
        "rating",
        "user_ratings_total",
        "photos",
        "types",
    ]
)
NYC_HINTS = ("new york", "nyc", "manhattan", "brooklyn", "queens", "bronx", "staten island")
NYC_CENTER = (40.7411, -73.9897)
DETAIL_ENRICH_LIMIT = 6
logger = logging.getLogger(__name__)


@dataclass
class GooglePlacesFetchResult:
    places: list[Place]
    attempted: bool
    succeeded: bool
    error: str | None = None


def fetch_and_cache_google_places(
    db: Session,
    *,
    query: str,
    lat: float | None,
    lng: float | None,
    radius_km: float | None,
    limit: int = 15,
) -> GooglePlacesFetchResult:
    if not query.strip():
        return GooglePlacesFetchResult(
            places=[], attempted=False, succeeded=False, error="Query is required"
        )

    if not settings.google_places_api_key:
        return GooglePlacesFetchResult(
            places=[],
            attempted=False,
            succeeded=False,
            error="Google Places API key is not configured",
        )

    params: dict[str, Any] = {
        "query": _query_with_city_hint(query),
        "region": "us",
        "language": "en",
        "key": settings.google_places_api_key,
    }
    if lat is not None and lng is not None:
        params["location"] = f"{lat},{lng}"
        if radius_km is not None:
            params["radius"] = min(50000, max(500, int(radius_km * 1000)))

    try:
        response = requests.get(GOOGLE_TEXT_SEARCH_URL, params=params, timeout=10)
        response.raise_for_status()
        payload: dict[str, Any] = response.json()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Google Places text search failed for %r: %s", query, exc)
        return GooglePlacesFetchResult(
            places=[],
            attempted=True,
            succeeded=False,
            error="Google Places search request failed",
        )

    status = payload.get("status", "UNKNOWN")
    if status == "ZERO_RESULTS":
        return GooglePlacesFetchResult(places=[], attempted=True, succeeded=True, error=None)
    if status != "OK":
        logger.warning("Google Places returned status %s for query %r", status, query)
        return GooglePlacesFetchResult(
            places=[],
            attempted=True,
            succeeded=False,
            error=f"Google Places returned status {status}",
        )

    cached: list[Place] = []
    fallback_lat = lat if lat is not None else NYC_CENTER[0]
    fallback_lng = lng if lng is not None else NYC_CENTER[1]

    for index, item in enumerate((payload.get("results") or [])[:limit]):
        details = None
        place_id = item.get("place_id")
        if index < DETAIL_ENRICH_LIMIT and isinstance(place_id, str) and place_id:
            details = _fetch_place_details(place_id)

        normalized = _normalize_google_result(
            item,
            details=details,
            fallback_lat=fallback_lat,
            fallback_lng=fallback_lng,
        )
        if not normalized:
            continue

        place = _upsert_google_place(db, normalized)
        if place is not None:
            cached.append(place)

    db.commit()
    return GooglePlacesFetchResult(places=cached, attempted=True, succeeded=True, error=None)


def _fetch_place_details(place_id: str) -> dict[str, Any] | None:
    try:
        response = requests.get(
            GOOGLE_DETAILS_URL,
            params={
                "place_id": place_id,
                "fields": DETAIL_FIELDS,
                "language": "en",
                "key": settings.google_places_api_key,
            },
            timeout=8,
        )
        response.raise_for_status()
        payload: dict[str, Any] = response.json()
    except Exception as exc:  # noqa: BLE001
        logger.info("Google Place Details lookup failed for %s: %s", place_id, exc)
        return None

    status = payload.get("status", "UNKNOWN")
    if status != "OK":
        logger.info("Google Place Details returned status %s for %s", status, place_id)
        return None
    return payload.get("result") if isinstance(payload.get("result"), dict) else None


def _query_with_city_hint(query: str) -> str:
    normalized = query.lower()
    if any(hint in normalized for hint in NYC_HINTS):
        return query
    return f"{query} NYC"


def _normalize_google_result(
    item: dict[str, Any],
    *,
    details: dict[str, Any] | None,
    fallback_lat: float,
    fallback_lng: float,
) -> dict[str, Any] | None:
    google_place_id = item.get("place_id") or (details or {}).get("place_id")
    name = item.get("name") or (details or {}).get("name")
    if not google_place_id or not name:
        return None

    details_payload = details or {}
    geometry = details_payload.get("geometry") or item.get("geometry") or {}
    location = geometry.get("location") or {}
    types = [
        value
        for value in (details_payload.get("types") or item.get("types") or [])
        if isinstance(value, str)
    ]
    formatted_address = (
        details_payload.get("formatted_address")
        or item.get("formatted_address")
        or item.get("vicinity")
    )
    lat = location.get("lat", fallback_lat)
    lng = location.get("lng", fallback_lng)
    price_level = (
        details_payload.get("price_level")
        if details_payload.get("price_level") is not None
        else item.get("price_level")
    )
    google_rating = (
        details_payload.get("rating")
        if details_payload.get("rating") is not None
        else item.get("rating")
    )
    google_user_ratings_total = (
        details_payload.get("user_ratings_total")
        if details_payload.get("user_ratings_total") is not None
        else item.get("user_ratings_total")
    )
    photos = details_payload.get("photos") or item.get("photos") or []
    photo_reference = None
    photo_metadata = None
    if isinstance(photos, list) and photos:
        candidate = photos[0]
        if isinstance(candidate, dict):
            photo_reference = candidate.get("photo_reference")
            photo_metadata = {
                "width": candidate.get("width"),
                "height": candidate.get("height"),
                "html_attributions": candidate.get("html_attributions"),
            }

    return {
        "google_place_id": google_place_id,
        "name": name,
        "formatted_address": formatted_address,
        "neighborhood": _extract_neighborhood(formatted_address),
        "lat": lat,
        "lng": lng,
        "price_level": price_level
        if isinstance(price_level, int) and 1 <= price_level <= 4
        else None,
        "place_type": _map_place_type(types),
        "google_primary_type": types[0] if types else None,
        "google_rating": float(google_rating) if isinstance(google_rating, (int, float)) else None,
        "google_user_ratings_total": (
            int(google_user_ratings_total)
            if isinstance(google_user_ratings_total, (int, float))
            and google_user_ratings_total >= 0
            else None
        ),
        "image_url": None,
        "google_photo_reference": photo_reference if isinstance(photo_reference, str) and photo_reference else None,
        "photo_source": "google_places" if photo_reference else None,
        "external_photo_metadata": photo_metadata,
        "phone": details_payload.get("formatted_phone_number"),
        "website": details_payload.get("website"),
        "tags": _google_tags(types),
        "external_raw_json": {
            "text_search": item,
            "details": details_payload or None,
        },
    }


def _map_place_type(types: list[str]) -> PlaceType:
    lowered = set(types)
    if lowered & {"event_venue", "concert_hall", "movie_theater", "night_club", "bar", "casino"}:
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
    return tags[:8]


def _extract_neighborhood(address: str | None) -> str | None:
    if not address:
        return None
    parts = [part.strip() for part in address.split(",") if part.strip()]
    if len(parts) >= 3:
        return parts[-3]
    if len(parts) >= 2:
        return parts[0]
    return parts[0] if parts else None


def _upsert_google_place(db: Session, payload: dict[str, Any]) -> Place | None:
    existing = db.scalar(select(Place).where(Place.google_place_id == payload["google_place_id"]))
    if not existing:
        existing = _find_similar_place(db, payload)

    if existing:
        if not existing.google_place_id:
            existing.google_place_id = payload["google_place_id"]
        if existing.source == PlaceSource.google:
            existing.name = payload["name"]
            existing.place_type = payload["place_type"]
            existing.lat = payload["lat"]
            existing.lng = payload["lng"]
        if payload.get("formatted_address") and (
            not existing.formatted_address or existing.source == PlaceSource.google
        ):
            existing.formatted_address = payload["formatted_address"]
        if payload.get("neighborhood") and (
            not existing.neighborhood or existing.source == PlaceSource.google
        ):
            existing.neighborhood = payload["neighborhood"]
        if payload.get("price_level") is not None and (
            existing.price_level is None or existing.source == PlaceSource.google
        ):
            existing.price_level = payload["price_level"]
        if payload.get("phone") and not existing.phone:
            existing.phone = payload["phone"]
        if payload.get("website") and not existing.website:
            existing.website = payload["website"]

        existing.google_primary_type = payload.get("google_primary_type")
        existing.google_rating = payload.get("google_rating")
        existing.google_user_ratings_total = payload.get("google_user_ratings_total")
        if payload.get("image_url") and (not existing.image_url or existing.source == PlaceSource.google):
            existing.image_url = payload.get("image_url")
        if payload.get("google_photo_reference") and (
            not existing.google_photo_reference or existing.source == PlaceSource.google
        ):
            existing.google_photo_reference = payload.get("google_photo_reference")
        if payload.get("photo_source") and (
            not existing.photo_source or existing.source == PlaceSource.google
        ):
            existing.photo_source = payload.get("photo_source")
        if payload.get("external_photo_metadata") and (
            not existing.external_photo_metadata or existing.source == PlaceSource.google
        ):
            existing.external_photo_metadata = payload.get("external_photo_metadata")
        if payload.get("google_photo_reference") or payload.get("image_url"):
            existing.image_last_synced_at = datetime.now(timezone.utc)
        existing.external_last_synced_at = datetime.now(timezone.utc)
        existing.external_raw_json = payload.get("external_raw_json")
        existing.is_cached_from_external = True

        _sync_tags(db, existing, payload["tags"])
        db.add(existing)
        db.flush()
        return existing

    place = Place(
        google_place_id=payload["google_place_id"],
        google_primary_type=payload.get("google_primary_type"),
        google_rating=payload.get("google_rating"),
        google_user_ratings_total=payload.get("google_user_ratings_total"),
        image_url=payload.get("image_url"),
        google_photo_reference=payload.get("google_photo_reference"),
        photo_source=payload.get("photo_source"),
        image_last_synced_at=datetime.now(timezone.utc)
        if payload.get("google_photo_reference") or payload.get("image_url")
        else None,
        external_photo_metadata=payload.get("external_photo_metadata"),
        source=PlaceSource.google,
        place_type=payload["place_type"],
        name=payload["name"],
        formatted_address=payload["formatted_address"],
        neighborhood=payload["neighborhood"],
        lat=payload["lat"],
        lng=payload["lng"],
        price_level=payload["price_level"],
        phone=payload.get("phone"),
        website=payload.get("website"),
        external_last_synced_at=datetime.now(timezone.utc),
        external_raw_json=payload.get("external_raw_json"),
        is_cached_from_external=True,
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
