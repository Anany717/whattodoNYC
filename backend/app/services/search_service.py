from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Place, PlaceSource, PlaceTag
from app.services.google_places import GooglePlacesFetchResult, fetch_and_cache_google_places
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
    search_source: Literal["live_google", "cached_google", "internal"]
    search_source_label: str
    is_live_result: bool
    source_priority: int


@dataclass
class SearchExecution:
    matches: list[SearchMatch]
    google_results_used: bool
    live_search_attempted: bool
    live_search_succeeded: bool
    live_result_count: int
    status_message: str | None


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
) -> SearchExecution:
    has_query = bool(query and query.strip())
    google_result = GooglePlacesFetchResult(places=[], attempted=False, succeeded=False, error=None)

    if has_query:
        google_result = fetch_and_cache_google_places(
            db,
            query=query or "things to do",
            lat=lat,
            lng=lng,
            radius_km=radius_km,
            limit=max(limit, 15),
        )

    live_result_place_ids = {place.id for place in google_result.places}
    matches = _rank_candidates(
        places=_load_search_places(db),
        query=query,
        lat=lat,
        lng=lng,
        radius_km=radius_km,
        price_level=price_level,
        tag=tag,
        open_now=open_now,
        live_result_place_ids=live_result_place_ids,
    )

    sorted_matches = _sort_matches(
        matches,
        sort_by=sort_by,
        has_query=has_query,
    )
    deduped_matches = _dedupe_matches(sorted_matches)
    return SearchExecution(
        matches=deduped_matches[:limit],
        google_results_used=bool(live_result_place_ids),
        live_search_attempted=google_result.attempted,
        live_search_succeeded=google_result.succeeded,
        live_result_count=len(live_result_place_ids),
        status_message=_build_status_message(has_query=has_query, google_result=google_result),
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
            .order_by(
                Place.external_last_synced_at.desc(),
                Place.updated_at.desc(),
                Place.created_at.desc(),
            )
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
    live_result_place_ids: set[str],
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
        search_source, search_source_label, source_priority = _search_source(
            place, live_result_place_ids
        )
        secondary_score = _secondary_score(
            distance_km=distance_km,
            average_rating_value=avg_rating,
            authenticity_score_value=auth_score,
            review_count_value=reviews,
            promotion_boost_value=promo_boost,
            source_priority=source_priority,
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
                    search_source=search_source,
                ),
                secondary_score=secondary_score,
                search_source=search_source,
                search_source_label=search_source_label,
                is_live_result=place.id in live_result_place_ids,
                source_priority=source_priority,
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
    primary_type = (place.google_primary_type or "").replace("_", "-").lower()

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

    coverage_bonus = token_hits / len(tokens)
    score += coverage_bonus * 4.2

    return min(1.0, score / max_score)


def _secondary_score(
    *,
    distance_km: float | None,
    average_rating_value: float | None,
    authenticity_score_value: float,
    review_count_value: int,
    promotion_boost_value: float,
    source_priority: int,
) -> float:
    distance_score = 0.4 if distance_km is None else min(1.0, 1 / (distance_km + 0.25) / 2)
    rating_score = (average_rating_value / 5) if average_rating_value is not None else 0.45
    review_volume_score = min(0.18, review_count_value * 0.015)
    source_bonus = source_priority * 0.04
    return round(
        (distance_score * 0.32)
        + (rating_score * 0.34)
        + (authenticity_score_value * 0.18)
        + review_volume_score
        + (promotion_boost_value * 0.08)
        + source_bonus,
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
    search_source: Literal["live_google", "cached_google", "internal"],
) -> str | None:
    reasons: list[tuple[float, str]] = []

    if search_source == "live_google":
        reasons.append((0.98, "fresh Google match"))
    elif search_source == "cached_google":
        reasons.append((0.45, "recently synced place data"))

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
                -item.source_priority,
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
                -item.source_priority,
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
                -item.source_priority,
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
                -item.source_priority,
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
                -item.source_priority,
                item.distance_km if item.distance_km is not None else float("inf"),
                item.place.name.lower(),
            ),
        )

    if has_query:
        return sorted(
            matches,
            key=lambda item: (
                -item.relevance_score,
                -item.source_priority,
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
            -item.source_priority,
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


def _search_source(
    place: Place,
    live_result_place_ids: set[str],
) -> tuple[Literal["live_google", "cached_google", "internal"], str, int]:
    if place.id in live_result_place_ids:
        return "live_google", "Live Google result", 2
    if place.is_cached_from_external or place.source == PlaceSource.google:
        return "cached_google", "Cached external place", 1
    return "internal", "Local catalog match", 0


def _build_status_message(*, has_query: bool, google_result: GooglePlacesFetchResult) -> str | None:
    if not has_query:
        return "Showing the local NYC catalog. Add keywords to trigger live Google search."
    if google_result.attempted and google_result.succeeded and google_result.places:
        return (
            "Live Google Places search is active for this query, "
            "with results cached and enriched by our local data."
        )
    if google_result.attempted and google_result.succeeded:
        return (
            "Google Places ran for this query, but there were no fresh matches. "
            "Showing cached/local results instead."
        )
    if google_result.error:
        if "configured" in google_result.error.lower():
            return (
                "Live Google search is not available in this environment yet. "
                "Showing cached/local results instead."
            )
        return "Live Google search is unavailable right now. Showing cached/local results instead."
    return "Showing cached/local results."


def _normalize_text(value: str | None) -> str:
    return " ".join((value or "").lower().replace("'", "").split())
