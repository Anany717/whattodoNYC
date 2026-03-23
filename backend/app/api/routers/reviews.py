from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.database import get_db
from app.models import Place, Review, User, UserRole
from app.schemas import ReviewCreate, ReviewOut, ReviewUpdate

router = APIRouter()


@router.post("/reviews", response_model=ReviewOut)
def create_or_update_review(
    payload: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.customer, UserRole.reviewer)),
) -> ReviewOut:
    place = db.get(Place, payload.place_id)
    if not place:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Place not found")

    review = db.scalar(
        select(Review).where(Review.user_id == current_user.id, Review.place_id == payload.place_id)
    )
    if review:
        review.rating_overall = payload.rating_overall
        review.rating_value = payload.rating_value
        review.rating_vibe = payload.rating_vibe
        review.rating_groupfit = payload.rating_groupfit
        review.comment = payload.comment
    else:
        review = Review(
            user_id=current_user.id,
            place_id=payload.place_id,
            rating_overall=payload.rating_overall,
            rating_value=payload.rating_value,
            rating_vibe=payload.rating_vibe,
            rating_groupfit=payload.rating_groupfit,
            comment=payload.comment,
        )
        db.add(review)

    db.commit()
    db.refresh(review)
    return ReviewOut.model_validate(review)


@router.put("/reviews/{review_id}", response_model=ReviewOut)
def update_review(
    review_id: str,
    payload: ReviewUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.customer, UserRole.reviewer)),
) -> ReviewOut:
    review = db.get(Review, review_id)
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    if review.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot edit another user's review",
        )

    review.rating_overall = payload.rating_overall
    review.rating_value = payload.rating_value
    review.rating_vibe = payload.rating_vibe
    review.rating_groupfit = payload.rating_groupfit
    review.comment = payload.comment

    db.add(review)
    db.commit()
    db.refresh(review)
    return ReviewOut.model_validate(review)


@router.delete("/reviews/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(
    review_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    review = db.get(Review, review_id)
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    if review.user_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete another user's review",
        )

    db.delete(review)
    db.commit()
