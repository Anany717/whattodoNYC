from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.database import get_db
from app.models import Place, Promotion, User, UserRole
from app.schemas import PlaceOut, PromotionOut

router = APIRouter()


@router.get("/seller/places", response_model=list[PlaceOut])
def get_seller_places(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.seller, UserRole.admin)),
) -> list[PlaceOut]:
    query = select(Place).order_by(Place.updated_at.desc())
    if current_user.role == UserRole.seller:
        query = query.where(Place.managed_by_user_id == current_user.id)
    else:
        query = query.where(Place.managed_by_user_id.is_not(None))
    places = list(db.scalars(query).all())
    return [PlaceOut.model_validate(place) for place in places]


@router.get("/seller/promotions", response_model=list[PromotionOut])
def get_seller_promotions(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.seller, UserRole.admin)),
) -> list[PromotionOut]:
    query = select(Promotion).order_by(Promotion.created_at.desc())
    if current_user.role == UserRole.seller:
        query = query.where(Promotion.seller_user_id == current_user.id)
    promotions = list(db.scalars(query).all())
    return [PromotionOut.model_validate(promo) for promo in promotions]
