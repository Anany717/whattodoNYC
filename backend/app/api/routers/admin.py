from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.database import get_db
from app.models import Place, Review, User, UserRole
from app.schemas import PlaceOut, ReviewOut, UserOut

router = APIRouter()


@router.get("/admin/users", response_model=list[UserOut])
def get_all_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.admin)),
) -> list[UserOut]:
    users = list(db.scalars(select(User).order_by(User.created_at.desc())).all())
    return [UserOut.model_validate(user) for user in users]


@router.get("/admin/places", response_model=list[PlaceOut])
def get_all_places(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.admin)),
) -> list[PlaceOut]:
    places = list(db.scalars(select(Place).order_by(Place.created_at.desc())).all())
    return [PlaceOut.model_validate(place) for place in places]


@router.get("/admin/reviews", response_model=list[ReviewOut])
def get_all_reviews(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.admin)),
) -> list[ReviewOut]:
    reviews = list(db.scalars(select(Review).order_by(Review.created_at.desc())).all())
    return [ReviewOut.model_validate(review) for review in reviews]
