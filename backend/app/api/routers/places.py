from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import require_roles
from app.core.database import get_db
from app.models import Place, PlaceSource, PlaceTag, Promotion, Review, User, UserRole
from app.schemas import PlaceCreate, PlaceOut, PlaceSearchOut, PromotionOut, ReviewOut
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
    places = list(
        db.scalars(
            select(Place)
            .options(selectinload(Place.tags).selectinload(PlaceTag.tag), selectinload(Place.hours))
            .order_by(Place.created_at.desc())
        ).all()
    )

    filtered: list[Place] = []
    now = datetime.now(timezone.utc)
    today = now.weekday() % 7

    for place in places:
        if query and query.lower() not in place.name.lower():
            continue
        if price_level and place.price_level and place.price_level != price_level:
            continue
        if tag:
            tags = {pt.tag.name.lower() for pt in place.tags if pt.tag}
            if tag.lower() not in tags:
                continue
        if lat is not None and lng is not None and radius_km is not None:
            distance = haversine_km(lat, lng, place.lat, place.lng)
            if distance > radius_km:
                continue
        if open_now is True and place.hours:
            day_rows = [hour for hour in place.hours if hour.day_of_week == today]
            if day_rows and all(row.is_closed for row in day_rows):
                continue

        filtered.append(place)

    return PlaceSearchOut(items=[PlaceOut.model_validate(item) for item in filtered])


@router.get("/places/{place_id}", response_model=PlaceOut)
def get_place(place_id: str, db: Session = Depends(get_db)) -> PlaceOut:
    place = db.get(Place, place_id)
    if not place:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Place not found")
    return PlaceOut.model_validate(place)


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
