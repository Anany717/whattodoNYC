from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    AuthenticityLabel,
    Place,
    PlaceTag,
)
from app.schemas import RecommendationItem, RecommendationRequest
from app.services.google_places import fetch_and_cache_google_places
from app.services.weather import get_weather_snapshot
from app.utils.geo import haversine_km


@dataclass
class ScoreBreakdown:
    keyword_relevance: float
    distance_score: float
    price_fit: float
    group_fit: float
    weather_fit: float
    review_strength: float
    authenticity_score: float
    promotion_boost: float


WEIGHTS = {
    "keyword_relevance": 0.20,
    "distance_score": 0.18,
    "price_fit": 0.14,
    "group_fit": 0.10,
    "weather_fit": 0.10,
    "review_strength": 0.14,
    "authenticity_score": 0.10,
    "promotion_boost": 0.04,
}


def get_recommendations(db: Session, req: RecommendationRequest) -> list[RecommendationItem]:
    candidates = _load_candidates(db)
    if len(candidates) < 10:
        fetch_and_cache_google_places(
            db,
            query=req.keywords,
            lat=req.lat,
            lng=req.lng,
            radius_km=req.radius_km,
            limit=20,
        )
        candidates = _load_candidates(db)

    weather = get_weather_snapshot(db, lat=req.lat, lng=req.lng)
    scored: list[tuple[RecommendationItem, float]] = []

    for place in candidates:
        distance_km = haversine_km(req.lat, req.lng, place.lat, place.lng)
        if distance_km > req.radius_km:
            continue
        if req.budget and place.price_level and place.price_level > req.budget:
            continue
        if not _is_open(place):
            continue
        if not _passes_preference_weather_filter(place, req.preference, weather):
            continue

        breakdown = _score_place(place=place, req=req, weather=weather, distance_km=distance_km)
        score = sum(WEIGHTS[key] * getattr(breakdown, key) for key in WEIGHTS)
        why = _build_why(breakdown)

        item = RecommendationItem(
            place_id=place.id,
            name=place.name,
            price_level=place.price_level,
            lat=place.lat,
            lng=place.lng,
            distance_km=round(distance_km, 2),
            score=round(score, 3),
            why=why,
        )
        scored.append((item, score))

    scored.sort(key=lambda entry: entry[1], reverse=True)
    return [item for item, _ in scored[:10]]


def _load_candidates(db: Session) -> list[Place]:
    query = (
        select(Place)
        .options(
            selectinload(Place.tags).selectinload(PlaceTag.tag),
            selectinload(Place.hours),
            selectinload(Place.reviews),
            selectinload(Place.authenticity_votes),
            selectinload(Place.promotions),
        )
        .order_by(Place.created_at.desc())
    )
    return list(db.scalars(query).all())


def _is_open(place: Place) -> bool:
    if not place.hours:
        return True

    now = datetime.now(timezone.utc)
    day = now.weekday() % 7
    current_time = now.time().replace(tzinfo=None)

    today = [hour for hour in place.hours if hour.day_of_week == day]
    if not today:
        return True

    for hour in today:
        if hour.is_closed:
            return False
        if hour.open_time is None or hour.close_time is None:
            return True
        if hour.open_time <= current_time <= hour.close_time:
            return True
    return False


def _score_place(
    *,
    place: Place,
    req: RecommendationRequest,
    weather: dict,
    distance_km: float,
) -> ScoreBreakdown:
    keyword = _keyword_relevance(place, req.keywords)
    distance_score = min(1.0, 1 / (distance_km + 0.1) / 2)
    price_fit = _price_fit(req.budget, place.price_level)
    group_fit = _group_fit(req.group_size, place)
    weather_fit = _weather_fit(req.preference, place, weather)
    review_strength = _review_strength(place)
    auth_score = _authenticity_score(place)
    promo_boost = _promotion_boost(place)

    return ScoreBreakdown(
        keyword_relevance=keyword,
        distance_score=distance_score,
        price_fit=price_fit,
        group_fit=group_fit,
        weather_fit=weather_fit,
        review_strength=review_strength,
        authenticity_score=auth_score,
        promotion_boost=promo_boost,
    )


def _keyword_relevance(place: Place, keywords: str) -> float:
    tokens = [token.strip().lower() for token in keywords.split() if token.strip()]
    if not tokens:
        return 0.0

    searchable = [place.name.lower(), place.place_type.value.lower()]
    if place.neighborhood:
        searchable.append(place.neighborhood.lower())
    if place.formatted_address:
        searchable.append(place.formatted_address.lower())
    for place_tag in place.tags:
        if place_tag.tag:
            searchable.append(place_tag.tag.name.lower())
    combined = " ".join(searchable)

    hits = sum(1 for token in tokens if token in combined)
    return hits / len(tokens)


def _price_fit(budget: int, price_level: int | None) -> float:
    if price_level is None:
        return 0.5
    diff = abs(budget - price_level)
    return max(0.0, 1.0 - diff / 3)


def _group_fit(group_size: int, place: Place) -> float:
    if not place.reviews:
        return 0.5

    group_ratings = [review.rating_groupfit for review in place.reviews if review.rating_groupfit is not None]
    if not group_ratings:
        return 0.5

    avg_group = sum(group_ratings) / len(group_ratings)
    normalized = avg_group / 5
    if group_size >= 6:
        return min(1.0, normalized + 0.05)
    if group_size == 1:
        return max(0.0, normalized - 0.05)
    return normalized


def _weather_fit(preference: str, place: Place, weather: dict) -> float:
    tags = {place_tag.tag.name.lower() for place_tag in place.tags if place_tag.tag}
    has_outdoor = "outdoor" in tags
    has_indoor = "indoor" in tags

    precipitation = bool(weather.get("precipitation"))

    if preference == "either":
        if precipitation and has_outdoor and not has_indoor:
            return 0.35
        return 0.8

    if preference == "indoor":
        if has_indoor:
            return 1.0
        if has_outdoor:
            return 0.3 if precipitation else 0.55
        return 0.65

    if preference == "outdoor":
        if has_outdoor:
            return 0.35 if precipitation else 1.0
        if has_indoor:
            return 0.3
        return 0.5

    return 0.5


def _passes_preference_weather_filter(place: Place, preference: str, weather: dict) -> bool:
    tags = {place_tag.tag.name.lower() for place_tag in place.tags if place_tag.tag}
    has_outdoor = "outdoor" in tags
    has_indoor = "indoor" in tags
    precipitation = bool(weather.get("precipitation"))

    if preference == "indoor":
        if has_outdoor and not has_indoor and precipitation:
            return False
        return True
    if preference == "outdoor":
        if has_indoor and not has_outdoor:
            return False
        return True
    return True


def _review_strength(place: Place) -> float:
    if not place.reviews:
        return 0.4
    avg = sum(review.rating_overall for review in place.reviews) / len(place.reviews)
    volume_boost = min(0.2, len(place.reviews) * 0.02)
    return min(1.0, (avg / 5) + volume_boost)


def _authenticity_score(place: Place) -> float:
    if not place.authenticity_votes:
        return 0.5

    authentic = sum(1 for vote in place.authenticity_votes if vote.label == AuthenticityLabel.authentic)
    touristy = sum(1 for vote in place.authenticity_votes if vote.label == AuthenticityLabel.touristy)
    total = authentic + touristy
    if total == 0:
        return 0.5
    return authentic / total


def _promotion_boost(place: Place) -> float:
    now = datetime.now(timezone.utc)
    active = [promo for promo in place.promotions if promo.start_at <= now <= promo.end_at]
    if not active:
        return 0.0
    boost = max(float(promo.boost_factor) for promo in active)
    return min(1.0, (boost - 1.0) / 2.0)


def _build_why(breakdown: ScoreBreakdown) -> str:
    labels = {
        "keyword_relevance": "strong keyword match",
        "distance_score": "close by",
        "price_fit": "good value for budget",
        "group_fit": "group-friendly",
        "weather_fit": "weather-friendly",
        "review_strength": "highly rated",
        "authenticity_score": "high authenticity",
        "promotion_boost": "active promotion",
    }

    factors = sorted(
        ((key, WEIGHTS[key] * getattr(breakdown, key)) for key in WEIGHTS),
        key=lambda item: item[1],
        reverse=True,
    )
    top = [labels[key] for key, value in factors if value > 0][:3]
    if not top:
        top = ["balanced fit"]
    return ", ".join(top)
