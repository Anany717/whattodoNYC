from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import Friendship, FriendshipStatus, User
from app.schemas import FriendRequestsOut, FriendsListEntry, FriendshipCreate, FriendshipOut, UserSummary

router = APIRouter()


def _friendship_query():
    return select(Friendship).options(
        selectinload(Friendship.requester),
        selectinload(Friendship.addressee),
    )


def _serialize_friendship(friendship: Friendship) -> FriendshipOut:
    return FriendshipOut(
        id=friendship.id,
        requester_user_id=friendship.requester_user_id,
        addressee_user_id=friendship.addressee_user_id,
        status=friendship.status,
        created_at=friendship.created_at,
        updated_at=friendship.updated_at,
        requester=UserSummary.model_validate(friendship.requester),
        addressee=UserSummary.model_validate(friendship.addressee),
    )


@router.get("/friends/search", response_model=list[UserSummary])
def search_users(
    query: str = Query(min_length=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[UserSummary]:
    users = list(
        db.scalars(
            select(User)
            .where(User.id != current_user.id)
            .where(or_(User.full_name.ilike(f"%{query}%"), User.email.ilike(f"%{query}%")))
            .order_by(User.full_name.asc())
            .limit(20)
        ).all()
    )
    return [UserSummary.model_validate(user) for user in users]


@router.get("/friends", response_model=list[FriendsListEntry])
def get_friends(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[FriendsListEntry]:
    friendships = list(
        db.scalars(
            _friendship_query()
            .where(Friendship.status == FriendshipStatus.accepted)
            .where(
                or_(
                    Friendship.requester_user_id == current_user.id,
                    Friendship.addressee_user_id == current_user.id,
                )
            )
            .order_by(Friendship.updated_at.desc())
        ).all()
    )

    entries: list[FriendsListEntry] = []
    for friendship in friendships:
        friend = (
            friendship.addressee
            if friendship.requester_user_id == current_user.id
            else friendship.requester
        )
        entries.append(
            FriendsListEntry(
                friendship_id=friendship.id,
                friend=UserSummary.model_validate(friend),
                created_at=friendship.created_at,
            )
        )
    return entries


@router.get("/friends/requests", response_model=FriendRequestsOut)
def get_friend_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FriendRequestsOut:
    incoming = list(
        db.scalars(
            _friendship_query()
            .where(Friendship.status == FriendshipStatus.pending)
            .where(Friendship.addressee_user_id == current_user.id)
            .order_by(Friendship.created_at.desc())
        ).all()
    )
    outgoing = list(
        db.scalars(
            _friendship_query()
            .where(Friendship.status == FriendshipStatus.pending)
            .where(Friendship.requester_user_id == current_user.id)
            .order_by(Friendship.created_at.desc())
        ).all()
    )
    return FriendRequestsOut(
        incoming=[_serialize_friendship(item) for item in incoming],
        outgoing=[_serialize_friendship(item) for item in outgoing],
    )


@router.post("/friends/request", response_model=FriendshipOut)
def create_friend_request(
    payload: FriendshipCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FriendshipOut:
    if payload.addressee_user_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot add yourself")

    addressee = db.get(User, payload.addressee_user_id)
    if not addressee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    existing = db.scalar(
        _friendship_query().where(
            or_(
                and_(
                    Friendship.requester_user_id == current_user.id,
                    Friendship.addressee_user_id == payload.addressee_user_id,
                ),
                and_(
                    Friendship.requester_user_id == payload.addressee_user_id,
                    Friendship.addressee_user_id == current_user.id,
                ),
            )
        )
    )

    if existing:
        if existing.status == FriendshipStatus.accepted:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You are already friends")
        if existing.status == FriendshipStatus.blocked:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Friend request unavailable")
        if (
            existing.status == FriendshipStatus.pending
            and existing.requester_user_id == payload.addressee_user_id
            and existing.addressee_user_id == current_user.id
        ):
            existing.status = FriendshipStatus.accepted
            db.add(existing)
            db.commit()
            db.refresh(existing)
            return _serialize_friendship(existing)

        existing.requester_user_id = current_user.id
        existing.addressee_user_id = payload.addressee_user_id
        existing.status = FriendshipStatus.pending
        db.add(existing)
        db.commit()
        db.refresh(existing)
        return _serialize_friendship(existing)

    friendship = Friendship(
        requester_user_id=current_user.id,
        addressee_user_id=payload.addressee_user_id,
        status=FriendshipStatus.pending,
    )
    db.add(friendship)
    db.commit()
    db.refresh(friendship)
    friendship = db.scalar(_friendship_query().where(Friendship.id == friendship.id))
    return _serialize_friendship(friendship)


@router.post("/friends/request/{request_id}/accept", response_model=FriendshipOut)
def accept_friend_request(
    request_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FriendshipOut:
    friendship = db.scalar(_friendship_query().where(Friendship.id == request_id))
    if not friendship:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Friend request not found")
    if friendship.addressee_user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the recipient can accept")
    if friendship.status != FriendshipStatus.pending:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Friend request is no longer pending")

    friendship.status = FriendshipStatus.accepted
    db.add(friendship)
    db.commit()
    db.refresh(friendship)
    return _serialize_friendship(friendship)


@router.post("/friends/request/{request_id}/decline", response_model=FriendshipOut)
def decline_friend_request(
    request_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FriendshipOut:
    friendship = db.scalar(_friendship_query().where(Friendship.id == request_id))
    if not friendship:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Friend request not found")
    if friendship.addressee_user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the recipient can decline")
    if friendship.status != FriendshipStatus.pending:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Friend request is no longer pending")

    friendship.status = FriendshipStatus.declined
    db.add(friendship)
    db.commit()
    db.refresh(friendship)
    return _serialize_friendship(friendship)


@router.delete("/friends/{friend_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_friend(
    friend_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    friendship = db.scalar(
        _friendship_query().where(
            Friendship.status == FriendshipStatus.accepted,
            or_(
                and_(
                    Friendship.requester_user_id == current_user.id,
                    Friendship.addressee_user_id == friend_id,
                ),
                and_(
                    Friendship.requester_user_id == friend_id,
                    Friendship.addressee_user_id == current_user.id,
                ),
            ),
        )
    )
    if not friendship:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Friend not found")

    db.delete(friendship)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
