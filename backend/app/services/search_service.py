from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Place, PlaceTag
from app.services.google_places import fetch_and_cache_google_places
from app.services.place_metrics import (
    active_promotion_boost,
    authenticity_score,
    average_rating,
    is_open_now,
    review_count,
    tag_names,
)
from app.utils.geo import haversine_km

SearchSortBy = Literal[
    "relevance",
    "price_asc",
    "price_desc",
    "rating_desc",
    "distance_asc",
    "authenticity_desc",
]


@dataclass
class SearchMatch:
    place: Place
    distance_km: float | None
    relevance_score: float
    average_rating: float | None
    authenticity_score: float
    review_count: int
    match_summary: str | None
    secondary_score: float


MIN_INTERNAL_MATCHES = 8
DEFAULT_LIMIT = 20


def run_place_search(
    db: Session,
    *,
    query: str | None,
    lat: float | None,
    lng: float | None,
    radius_km: float | None,
    price_level: int | None,
    tag: str | None,
    open_now: bool | None,
    sort_by: SearchSortBy,
    limit: int = DEFAULT_LIMIT,
) -> tuple[list[SearchMatch], bool]:
    matches = _rank_candidates(
        places=_load_search_places(db),
        query=query,
        lat=lat,
        lng=lng,
        radius_km=radius_km,
        price_level=price_level,
        tag=tag,
        open_now=open_now,
    )

    google_results_used = False
    if _should_fetch_google(query=query, lat=lat, lng=lng, matches=matches):
        fetched = fetch_and_cache_google_places(
            db,
            query=query or "things to do",
            lat=lat or 40.7411,
            lng=lng or -73.9897,
            radius_km=radius_km or 5,
            limit=max(limit, 15),
        )
        if fetched:
            google_results_used = True
            matches = _rank_candidates(
                places=_load_search_places(db),
                query=query,
                lat=lat,
                lng=lng,
                radius_km=radius_km,
                price_level=price_level,
                tag=tag,
                open_now=open_now,
            )

    sorted_matches = _sort_matches(
        matches,
        sort_by=sort_by,
        has_query=bool(query and query.strip()),
    )
    deduped_matches = _dedupe_matches(sorted_matches)
    return deduped_matches[:limit], google_results_used


def _should_fetch_google(
    *,
    query: str | None,
    lat: float | None,
    lng: float | None,
    matches: list[SearchMatch],
) -> bool:
    return bool(
        query
        and query.strip()
        and lat is not None
        and lng is not None
        and len(matches) < MIN_INTERNAL_MATCHES
    )


def _load_search_places(db: Session) -> list[Place]:
    return list(
        db.scalars(
            select(Place)
            .options(
                selectinload(Place.tags).selectinload(PlaceTag.tag),
                selectinload(Place.hours),
                selectinload(Place.reviews),
                selectinload(Place.authenticity_votes),
                selectinload(Place.promotions),
            )
            .order_by(Place.updated_at.desc(), Place.created_at.desc())
        ).all()
    )


def _rank_candidates(
    *,
    places: list[Place],
    query: str | None,
    lat: float | None,
    lng: float | None,
    radius_km: float | None,
    price_level: int | None,
    tag: str | None,
    open_now: bool | None,
) -> list[SearchMatch]:
    normalized_tag = tag.lower().strip() if tag else None
    matches: list[SearchMatch] = []

    for place in places:
        tags = tag_names(place)
        relevance = _keyword_relevance(place, query, tags)
        if query and query.strip() and relevance <= 0:
            continue
        if price_level and place.price_level and place.price_level != price_level:
            continue
        if normalized_tag and normalized_tag not in tags:
            continue
        if open_now is True and not is_open_now(place):
            continue

        distance_km: float | None = None
        if lat is not None and lng is not None:
            distance_km = haversine_km(lat, lng, place.lat, place.lng)
            if radius_km is not None and distance_km > radius_km:
                continue

        avg_rating = average_rating(place)
        auth_score = authenticity_score(place)
        reviews = review_count(place)
        promo_boost = active_promotion_boost(place)
        secondary_score = _secondary_score(
            distance_km=distance_km,
            average_rating_value=avg_rating,
            authenticity_score_value=auth_score,
            review_count_value=reviews,
            promotion_boost_value=promo_boost,
        )

        matches.append(
            SearchMatch(
                place=place,
                distance_km=round(distance_km, 2) if distance_km is not None else None,
                relevance_score=round(relevance, 3),
                average_rating=avg_rating,
                authenticity_score=auth_score,
                review_count=reviews,
                match_summary=_build_match_summary(
                    place=place,
                    relevance_score=relevance,
                    distance_km=distance_km,
                    average_rating_value=avg_rating,
                    authenticity_score_value=auth_score,
                    promotion_boost_value=promo_boost,
                ),
                secondary_score=secondary_score,
            )
        )

    return matches


def _keyword_relevance(place: Place, query: str | None, tags: list[str]) -> float:
    if not query or not query.strip():
        return 0.0

    normalized_query = " ".join(query.lower().split())
    tokens = [token for token in normalized_query.replace(",", " ").split() if token]
    if not tokens:
        return 0.0

    name = place.name.lower()
    place_type = place.place_type.value.lower()
    neighborhood = (place.neighborhood or "").lower()
    address = (place.formatted_address or "").lower()

    score = 0.0
    max_score = 10.0 + (len(tokens) * 4.5)

    if normalized_query in name:
        score += 8.0
    elif any(token in name for token in tokens):
        score += 2.0

    if normalized_query in " ".join(tags):
        score += 4.0
    if normalized_query == place_type:
        score += 4.0
    elif normalized_query in place_type:
        score += 2.5
    if normalized_query in neighborhood:
        score += 2.5
    if normalized_query in address:
        score += 2.0

    token_hits = 0
    for token in tokens:
        token_score = 0.0
        if token in name:
            token_score += 3.0
        if any(token in tag for tag in tags):
            token_score += 2.8
        if token == place_type or token in place_type:
            token_score += 2.3
        if token in neighborhood:
            token_score += 1.6
        if token in address:
            token_score += 1.1
        if token_score > 0:
            token_hits += 1
        score += token_score

    coverage_bonus = token_hits / len(tokens)
    score += coverage_bonus * 3.0

    return min(1.0, score / max_score)


def _secondary_score(
    *,
    distance_km: float | None,
    average_rating_value: float | None,
    authenticity_score_value: float,
    review_count_value: int,
    promotion_boost_value: float,
) -> float:
    distance_score = 0.4 if distance_km is None else min(1.0, 1 / (distance_km + 0.25) / 2)
    rating_score = (average_rating_value / 5) if average_rating_value is not None else 0.45
    review_volume_score = min(0.15, review_count_value * 0.02)
    return round(
        (distance_score * 0.35)
        + (rating_score * 0.35)
        + (authenticity_score_value * 0.2)
        + review_volume_score
        + (promotion_boost_value * 0.1),
        3,
    )


def _build_match_summary(
    *,
    place: Place,
    relevance_score: float,
    distance_km: float | None,
    average_rating_value: float | None,
    authenticity_score_value: float,
    promotion_boost_value: float,
) -> str | None:
    reasons: list[tuple[float, str]] = []

    if relevance_score >= 0.6:
        reasons.append((relevance_score, "strong keyword match"))
    elif relevance_score >= 0.35:
        reasons.append((relevance_score, "matches your search"))

    if distance_km is not None and distance_km <= 1.5:
        reasons.append((0.9, "very close by"))
    elif distance_km is not None and distance_km <= 4:
        reasons.append((0.6, "near your location"))

    if average_rating_value is not None and average_rating_value >= 4.5:
        reasons.append((average_rating_value / 5, "highly rated"))

    if authenticity_score_value >= 0.7:
        reasons.append((authenticity_score_value, "strong authenticity"))

    if promotion_boost_value > 0:
        reasons.append((promotion_boost_value, "active promotion"))

    if place.price_level is not None and place.price_level <= 2:
        reasons.append((0.45, "budget-friendly"))

    reasons.sort(key=lambda item: item[0], reverse=True)
    if not reasons:
        return None
    return ", ".join(label for _, label in reasons[:3])


def _sort_matches(
    matches: list[SearchMatch],
    *,
    sort_by: SearchSortBy,
    has_query: bool,
) -> list[SearchMatch]:
    if sort_by == "price_asc":
        return sorted(
            matches,
            key=lambda item: (
                item.place.price_level is None,
                item.place.price_level or 99,
                -item.relevance_score,
                item.distance_km if item.distance_km is not None else float("inf"),
                item.place.name.lower(),
            ),
        )

    if sort_by == "price_desc":
        return sorted(
            matches,
            key=lambda item: (
                item.place.price_level is None,
                -(item.place.price_level or 0),
                -item.relevance_score,
                item.distance_km if item.distance_km is not None else float("inf"),
                item.place.name.lower(),
            ),
        )

    if sort_by == "rating_desc":
        return sorted(
            matches,
            key=lambda item: (
                item.average_rating is None,
                -(item.average_rating or 0),
                -item.relevance_score,
                item.distance_km if item.distance_km is not None else float("inf"),
                item.place.name.lower(),
            ),
        )

    if sort_by == "distance_asc":
        return sorted(
            matches,
            key=lambda item: (
                item.distance_km is None,
                item.distance_km if item.distance_km is not None else float("inf"),
                -item.relevance_score,
                -item.secondary_score,
                item.place.name.lower(),
            ),
        )

    if sort_by == "authenticity_desc":
        return sorted(
            matches,
            key=lambda item: (
                -item.authenticity_score,
                -item.relevance_score,
                item.distance_km if item.distance_km is not None else float("inf"),
                item.place.name.lower(),
            ),
        )

    if has_query:
        return sorted(
            matches,
            key=lambda item: (
                -item.relevance_score,
                -item.secondary_score,
                item.distance_km if item.distance_km is not None else float("inf"),
                item.place.name.lower(),
            ),
        )

    return sorted(
        matches,
        key=lambda item: (
            item.distance_km is None,
            item.distance_km if item.distance_km is not None else float("inf"),
            -(item.average_rating or 0),
            -item.authenticity_score,
            item.place.name.lower(),
        ),
    )


def _dedupe_matches(matches: list[SearchMatch]) -> list[SearchMatch]:
    deduped: list[SearchMatch] = []
    for match in matches:
        if any(_is_duplicate(existing, match) for existing in deduped):
            continue
        deduped.append(match)
    return deduped


def _is_duplicate(left: SearchMatch, right: SearchMatch) -> bool:
    if left.place.id == right.place.id:
        return True
    if left.place.google_place_id and left.place.google_place_id == right.place.google_place_id:
        return True

    left_name = _normalize_text(left.place.name)
    right_name = _normalize_text(right.place.name)
    if left_name != right_name:
        return False

    left_address = _normalize_text(left.place.formatted_address)
    right_address = _normalize_text(right.place.formatted_address)
    if left_address and right_address and left_address == right_address:
        return True

    return haversine_km(left.place.lat, left.place.lng, right.place.lat, right.place.lng) <= 0.15


def _normalize_text(value: str | None) -> str:
    return " ".join((value or "").lower().replace("'", "").split())
