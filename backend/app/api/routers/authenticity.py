from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.database import get_db
from app.models import AuthenticityLabel, AuthenticityVote, Place, User, UserRole
from app.schemas import AuthenticityOut, AuthenticityVoteIn

router = APIRouter()


@router.post("/authenticity/vote", response_model=AuthenticityOut)
def vote_authenticity(
    payload: AuthenticityVoteIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.customer, UserRole.reviewer)),
) -> AuthenticityOut:
    place = db.get(Place, payload.place_id)
    if not place:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Place not found")

    vote = db.scalar(
        select(AuthenticityVote).where(
            AuthenticityVote.user_id == current_user.id,
            AuthenticityVote.place_id == payload.place_id,
        )
    )
    if vote:
        vote.label = payload.label
    else:
        vote = AuthenticityVote(user_id=current_user.id, place_id=payload.place_id, label=payload.label)
        db.add(vote)

    db.commit()
    return _summary(db, payload.place_id)


@router.get("/places/{place_id}/authenticity", response_model=AuthenticityOut)
def get_authenticity(place_id: str, db: Session = Depends(get_db)) -> AuthenticityOut:
    place = db.get(Place, place_id)
    if not place:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Place not found")
    return _summary(db, place_id)


def _summary(db: Session, place_id: str) -> AuthenticityOut:
    votes = list(db.scalars(select(AuthenticityVote).where(AuthenticityVote.place_id == place_id)).all())
    authentic_count = sum(1 for vote in votes if vote.label == AuthenticityLabel.authentic)
    touristy_count = sum(1 for vote in votes if vote.label == AuthenticityLabel.touristy)
    total = authentic_count + touristy_count
    score = round((authentic_count / total) if total else 0.5, 3)
    return AuthenticityOut(
        place_id=place_id,
        authentic_count=authentic_count,
        touristy_count=touristy_count,
        score=score,
    )
