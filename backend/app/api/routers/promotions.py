from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.database import get_db
from app.models import Place, Promotion, User, UserRole
from app.schemas import PromotionCreate, PromotionOut

router = APIRouter()


@router.post("/promotions", response_model=PromotionOut)
def create_promotion(
    payload: PromotionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.seller)),
) -> PromotionOut:
    place = db.get(Place, payload.place_id)
    if not place:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Place not found")
    if place.managed_by_user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You must claim this place first")

    promo = Promotion(
        place_id=payload.place_id,
        seller_user_id=current_user.id,
        title=payload.title,
        description=payload.description,
        boost_factor=payload.boost_factor,
        start_at=payload.start_at,
        end_at=payload.end_at,
    )
    db.add(promo)
    db.commit()
    db.refresh(promo)
    return PromotionOut.model_validate(promo)
