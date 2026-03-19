from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import require_roles
from app.core.database import get_db
from app.models import AuthenticityLabel, Place, PlaceSource, PlaceTag, Promotion, Review, User, UserRole
from app.schemas import PlaceCreate, PlaceDetailOut, PlaceOut, PlaceSearchOut, PromotionOut, ReviewOut
from app.services.google_places import fetch_and_cache_google_places
from app.utils.geo import haversine_km

router = APIRouter()


@router.get("/places/search", response_model=PlaceSearchOut)
def search_places(
    query: str | None = Query(default=None),
    lat: float | None = Query(default=None),
    lng: float | None = Query(default=None),
    radius_km: float | None = Query(default=5),
    price_level: int | None = Query(default=None, ge=1, le=4),
    tag: str | None = Query(default=None),
    open_now: bool | None = Query(default=None),
    db: Session = Depends(get_db),
) -> PlaceSearchOut:
    places = _load_search_places(db)
    ranked = _rank_places(
        places=places,
        query=query,
        lat=lat,
        lng=lng,
        radius_km=radius_km,
        price_level=price_level,
        tag=tag,
        open_now=open_now,
    )

    if query and lat is not None and lng is not None and len(ranked) < 8:
        fetched = fetch_and_cache_google_places(
            db,
            query=query,
            lat=lat,
            lng=lng,
            radius_km=radius_km or 5,
            limit=20,
        )
        if fetched:
            places = _load_search_places(db)
            ranked = _rank_places(
                places=places,
                query=query,
                lat=lat,
                lng=lng,
                radius_km=radius_km,
                price_level=price_level,
                tag=tag,
                open_now=open_now,
            )

    if query:
        ranked.sort(key=lambda item: (-item[1], item[2], item[0].name.lower()))
    elif lat is not None and lng is not None:
        ranked.sort(key=lambda item: (item[2], item[0].name.lower()))
    else:
        ranked.sort(key=lambda item: item[0].name.lower())

    return PlaceSearchOut(items=[PlaceOut.model_validate(place) for place, _, _ in ranked])


@router.get("/places/{place_id}", response_model=PlaceDetailOut)
def get_place(place_id: str, db: Session = Depends(get_db)) -> PlaceDetailOut:
    place = db.scalar(
        select(Place)
        .where(Place.id == place_id)
        .options(
            selectinload(Place.tags).selectinload(PlaceTag.tag),
            selectinload(Place.reviews),
            selectinload(Place.authenticity_votes),
        )
    )
    if not place:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Place not found")

    tags = [place_tag.tag.name for place_tag in place.tags if place_tag.tag]
    review_count = len(place.reviews)
    average_rating = (
        round(sum(review.rating_overall for review in place.reviews) / review_count, 2)
        if review_count
        else None
    )
    authentic_count = sum(
        1 for vote in place.authenticity_votes if vote.label == AuthenticityLabel.authentic
    )
    touristy_count = sum(
        1 for vote in place.authenticity_votes if vote.label == AuthenticityLabel.touristy
    )
    total_votes = authentic_count + touristy_count
    authenticity_score = round(authentic_count / total_votes, 3) if total_votes else 0.5

    return PlaceDetailOut(
        id=place.id,
        name=place.name,
        formatted_address=place.formatted_address,
        neighborhood=place.neighborhood,
        place_type=place.place_type,
        price_level=place.price_level,
        phone=place.phone,
        website=place.website,
        lat=place.lat,
        lng=place.lng,
        tags=tags,
        average_rating=average_rating,
        authenticity_score=authenticity_score,
        review_count=review_count,
    )


@router.post("/places", response_model=PlaceOut)
def create_place(
    payload: PlaceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.seller, UserRole.admin)),
) -> PlaceOut:
    place = Place(
        source=PlaceSource.internal,
        place_type=payload.place_type,
        name=payload.name,
        formatted_address=payload.formatted_address,
        neighborhood=payload.neighborhood,
        lat=payload.lat,
        lng=payload.lng,
        price_level=payload.price_level,
        phone=payload.phone,
        website=payload.website,
        managed_by_user_id=current_user.id if current_user.role == UserRole.seller else None,
    )
    db.add(place)
    db.commit()
    db.refresh(place)
    return PlaceOut.model_validate(place)


@router.post("/places/{place_id}/claim", response_model=PlaceOut)
def claim_place(
    place_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.seller)),
) -> PlaceOut:
    place = db.get(Place, place_id)
    if not place:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Place not found")
    if place.managed_by_user_id and place.managed_by_user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Place already claimed")

    place.managed_by_user_id = current_user.id
    db.add(place)
    db.commit()
    db.refresh(place)
    return PlaceOut.model_validate(place)


@router.get("/places/{place_id}/reviews", response_model=list[ReviewOut])
def place_reviews(place_id: str, db: Session = Depends(get_db)) -> list[ReviewOut]:
    reviews = list(
        db.scalars(select(Review).where(Review.place_id == place_id).order_by(Review.created_at.desc())).all()
    )
    return [ReviewOut.model_validate(item) for item in reviews]


@router.get("/places/{place_id}/promotions", response_model=list[PromotionOut])
def place_promotions(place_id: str, db: Session = Depends(get_db)) -> list[PromotionOut]:
    now = datetime.now(timezone.utc)
    promotions = list(
        db.scalars(
            select(Promotion)
            .where(Promotion.place_id == place_id)
            .where(Promotion.start_at <= now)
            .where(Promotion.end_at >= now)
            .order_by(Promotion.start_at.desc())
        ).all()
    )
    return [PromotionOut.model_validate(item) for item in promotions]


def _load_search_places(db: Session) -> list[Place]:
    return list(
        db.scalars(
            select(Place)
            .options(selectinload(Place.tags).selectinload(PlaceTag.tag), selectinload(Place.hours))
            .order_by(Place.created_at.desc())
        ).all()
    )


def _rank_places(
    *,
    places: list[Place],
    query: str | None,
    lat: float | None,
    lng: float | None,
    radius_km: float | None,
    price_level: int | None,
    tag: str | None,
    open_now: bool | None,
) -> list[tuple[Place, float, float]]:
    ranked: list[tuple[Place, float, float]] = []
    today = datetime.now(timezone.utc).weekday() % 7
    normalized_tag = tag.lower().strip() if tag else None

    for place in places:
        tag_names = _tag_names(place)
        relevance = _search_relevance(place, query, tag_names)
        if query and relevance <= 0:
            continue
        if price_level and place.price_level and place.price_level != price_level:
            continue
        if normalized_tag and not any(normalized_tag in tag_name for tag_name in tag_names):
            continue

        distance_km = float("inf")
        if lat is not None and lng is not None:
            distance_km = haversine_km(lat, lng, place.lat, place.lng)
            if radius_km is not None and distance_km > radius_km:
                continue
        if open_now is True and place.hours:
            day_rows = [hour for hour in place.hours if hour.day_of_week == today]
            if day_rows and all(row.is_closed for row in day_rows):
                continue

        ranked.append((place, relevance, distance_km))

    return ranked


def _tag_names(place: Place) -> list[str]:
    return [place_tag.tag.name.lower() for place_tag in place.tags if place_tag.tag]


def _search_relevance(place: Place, query: str | None, tag_names: list[str]) -> float:
    if not query or not query.strip():
        return 0.0

    normalized_query = query.strip().lower()
    tokens = [token for token in normalized_query.replace(",", " ").split() if token]

    name = place.name.lower()
    neighborhood = (place.neighborhood or "").lower()
    address = (place.formatted_address or "").lower()
    place_type = place.place_type.value.lower()

    score = 0.0
    if normalized_query in name:
        score += 5.0
    if normalized_query in neighborhood or normalized_query in address:
        score += 2.5
    if normalized_query == place_type:
        score += 2.0

    for token in tokens:
        if token in name:
            score += 2.2
        if token in neighborhood:
            score += 1.5
        if token in address:
            score += 1.2
        if token in place_type:
            score += 1.3
        if any(token in tag_name for tag_name in tag_names):
            score += 1.8

    return score / max(1, len(tokens))
