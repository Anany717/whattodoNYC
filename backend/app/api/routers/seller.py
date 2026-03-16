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
    current_user: User = Depends(require_roles(UserRole.seller)),
) -> list[PlaceOut]:
    places = list(
        db.scalars(
            select(Place).where(Place.managed_by_user_id == current_user.id).order_by(Place.updated_at.desc())
        ).all()
    )
    return [PlaceOut.model_validate(place) for place in places]


@router.get("/seller/promotions", response_model=list[PromotionOut])
def get_seller_promotions(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.seller)),
) -> list[PromotionOut]:
    promotions = list(
        db.scalars(
            select(Promotion)
            .where(Promotion.seller_user_id == current_user.id)
            .order_by(Promotion.created_at.desc())
        ).all()
    )
    return [PromotionOut.model_validate(promo) for promo in promotions]
