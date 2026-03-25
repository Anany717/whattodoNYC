from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import require_roles
from app.core.database import get_db
from app.models import Place, PlaceSource, PlaceTag, Promotion, Review, User, UserRole
from app.schemas import (
    PlaceCreate,
    PlaceDetailOut,
    PlaceOut,
    PlaceSearchItemOut,
    PlaceSearchOut,
    PromotionOut,
    ReviewOut,
    SearchSortBy,
)
from app.services.place_metrics import authenticity_score, average_rating, review_count
from app.services.search_service import run_place_search

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
    sort_by: SearchSortBy = Query(default="relevance"),
    db: Session = Depends(get_db),
) -> PlaceSearchOut:
    search_run = run_place_search(
        db,
        query=query,
        lat=lat,
        lng=lng,
        radius_km=radius_km,
        price_level=price_level,
        tag=tag,
        open_now=open_now,
        sort_by=sort_by,
    )

    items = [
        PlaceSearchItemOut(
            **PlaceOut.model_validate(match.place).model_dump(),
            distance_km=match.distance_km,
            average_rating=match.average_rating,
            authenticity_score=match.authenticity_score,
            review_count=match.review_count,
            relevance_score=match.relevance_score,
            match_summary=match.match_summary,
            search_source=match.search_source,
            search_source_label=match.search_source_label,
            is_live_result=match.is_live_result,
        )
        for match in search_run.matches
    ]
    return PlaceSearchOut(
        items=items,
        sort_by=sort_by,
        google_results_used=search_run.google_results_used,
        live_search_attempted=search_run.live_search_attempted,
        live_search_succeeded=search_run.live_search_succeeded,
        live_result_count=search_run.live_result_count,
        status_message=search_run.status_message,
    )


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
    return PlaceDetailOut(
        id=place.id,
        google_place_id=place.google_place_id,
        google_primary_type=place.google_primary_type,
        google_rating=place.google_rating,
        google_user_ratings_total=place.google_user_ratings_total,
        image_url=place.image_url,
        google_photo_reference=place.google_photo_reference,
        photo_source=place.photo_source,
        image_last_synced_at=place.image_last_synced_at,
        name=place.name,
        formatted_address=place.formatted_address,
        neighborhood=place.neighborhood,
        place_type=place.place_type,
        price_level=place.price_level,
        phone=place.phone,
        website=place.website,
        lat=place.lat,
        lng=place.lng,
        external_last_synced_at=place.external_last_synced_at,
        is_seed_data=place.is_seed_data,
        is_cached_from_external=place.is_cached_from_external,
        tags=tags,
        average_rating=average_rating(place),
        authenticity_score=authenticity_score(place),
        review_count=review_count(place),
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
        db.scalars(
            select(Review).where(Review.place_id == place_id).order_by(Review.created_at.desc())
        ).all()
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
