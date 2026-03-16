from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.security import hash_password
from app.models import Place, Review, User
from app.schemas import UserOut, UserReviewOut, UserUpdate

router = APIRouter()


@router.get("/users/me", response_model=UserOut)
def get_my_profile(current_user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(current_user)


@router.put("/users/me", response_model=UserOut)
def update_my_profile(
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserOut:
    if payload.full_name:
        current_user.full_name = payload.full_name
    if payload.password:
        current_user.password_hash = hash_password(payload.password)

    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return UserOut.model_validate(current_user)


@router.get("/users/me/reviews", response_model=list[UserReviewOut])
def get_my_reviews(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[UserReviewOut]:
    rows = db.execute(
        select(Review, Place.name)
        .join(Place, Place.id == Review.place_id)
        .where(Review.user_id == current_user.id)
        .order_by(Review.created_at.desc())
    ).all()

    response: list[UserReviewOut] = []
    for review, place_name in rows:
        response.append(
            UserReviewOut(
                id=review.id,
                user_id=review.user_id,
                place_id=review.place_id,
                place_name=place_name,
                rating_overall=review.rating_overall,
                rating_value=review.rating_value,
                rating_vibe=review.rating_vibe,
                rating_groupfit=review.rating_groupfit,
                comment=review.comment,
                created_at=review.created_at,
            )
        )
    return response
