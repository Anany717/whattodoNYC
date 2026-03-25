from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Place, PlaceTag
from app.schemas import RecommendationItem, RecommendationRequest
from app.services.google_places import fetch_and_cache_google_places
from app.services.place_metrics import (
    active_promotion_boost,
    authenticity_score,
    average_rating,
    is_open_now,
    tag_names,
)
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
    "keyword_relevance": 0.48,
    "distance_score": 0.12,
    "price_fit": 0.09,
    "group_fit": 0.07,
    "weather_fit": 0.06,
    "review_strength": 0.08,
    "authenticity_score": 0.06,
    "promotion_boost": 0.04,
}


def get_recommendations(db: Session, req: RecommendationRequest) -> list[RecommendationItem]:
    if req.keywords.strip():
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
        if not is_open_now(place):
            continue
        if not _passes_preference_weather_filter(place, req.preference, weather):
            continue

        breakdown = _score_place(place=place, req=req, weather=weather, distance_km=distance_km)
        if req.keywords.strip() and breakdown.keyword_relevance < 0.12:
            continue
        score = sum(WEIGHTS[key] * getattr(breakdown, key) for key in WEIGHTS)
        why = _build_why(breakdown)

        item = RecommendationItem(
            place_id=place.id,
            name=place.name,
            place_type=place.place_type,
            price_level=place.price_level,
            formatted_address=place.formatted_address,
            source=place.source,
            google_rating=place.google_rating,
            google_user_ratings_total=place.google_user_ratings_total,
            image_url=place.image_url,
            google_photo_reference=place.google_photo_reference,
            photo_source=place.photo_source,
            is_cached_from_external=place.is_cached_from_external,
            lat=place.lat,
            lng=place.lng,
            distance_km=round(distance_km, 2),
            score=round(score, 3),
            why=why,
        )
        scored.append((item, score))

    scored.sort(key=lambda entry: (entry[1], entry[0].distance_km * -1), reverse=True)
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
        .order_by(Place.updated_at.desc(), Place.created_at.desc())
    )
    return list(db.scalars(query).all())


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
    auth_score = authenticity_score(place)
    promo_boost = active_promotion_boost(place)

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
    normalized_query = " ".join(keywords.lower().split())
    tokens = [token for token in normalized_query.replace(",", " ").split() if token]
    if not tokens:
        return 0.0

    name = place.name.lower()
    place_type = place.place_type.value.lower()
    neighborhood = (place.neighborhood or "").lower()
    address = (place.formatted_address or "").lower()
    primary_type = (place.google_primary_type or "").replace("_", "-").lower()
    tags = tag_names(place)

    score = 0.0
    max_score = 12.0 + (len(tokens) * 5.2)

    if normalized_query in name:
        score += 9.5
    elif any(token in name for token in tokens):
        score += 2.5

    if normalized_query in " ".join(tags):
        score += 5.5
    if normalized_query == place_type:
        score += 4.5
    elif normalized_query in place_type:
        score += 3.0
    if normalized_query in neighborhood:
        score += 3.0
    if normalized_query in address:
        score += 2.4
    if normalized_query in primary_type:
        score += 2.2

    token_hits = 0
    for token in tokens:
        token_score = 0.0
        if token in name:
            token_score += 3.3
        if any(token in tag for tag in tags):
            token_score += 3.1
        if token == place_type or token in place_type:
            token_score += 2.5
        if token in neighborhood:
            token_score += 1.8
        if token in address:
            token_score += 1.3
        if token in primary_type:
            token_score += 1.6
        if token_score > 0:
            token_hits += 1
        score += token_score

    score += (token_hits / len(tokens)) * 4.2
    return min(1.0, score / max_score)


def _price_fit(budget: int, price_level: int | None) -> float:
    if price_level is None:
        return 0.5
    diff = abs(budget - price_level)
    return max(0.0, 1.0 - diff / 3)


def _group_fit(group_size: int, place: Place) -> float:
    if not place.reviews:
        return 0.5

    group_ratings = [
        review.rating_groupfit for review in place.reviews if review.rating_groupfit is not None
    ]
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
    tags = set(tag_names(place))
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
    tags = set(tag_names(place))
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
    place_average_rating = average_rating(place)
    if place_average_rating is None:
        return 0.4
    volume_boost = min(0.2, len(place.reviews) * 0.02)
    return min(1.0, (place_average_rating / 5) + volume_boost)


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
