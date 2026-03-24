from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import (
    Friendship,
    FriendshipStatus,
    Plan,
    PlanItem,
    PlanItemVote,
    PlanMember,
    PlanMemberRole,
    PlanStatus,
    Place,
    User,
)
from app.schemas import (
    FinalChoiceOut,
    PlanCreate,
    PlanFinalizeCreate,
    PlanInviteCreate,
    PlanItemCreate,
    PlanItemOut,
    PlanMemberOut,
    PlanOut,
    PlanSummaryOut,
    PlanUpdate,
    PlanVoteCreate,
    PlanVotesSummaryOut,
)
from app.services.plans import (
    get_member,
    get_plan_with_details,
    is_plan_member,
    serialize_final_choice,
    serialize_item,
    serialize_member,
    serialize_plan,
    serialize_plan_summary,
    serialize_votes_summary,
)

router = APIRouter()


def _get_plan_or_404(db: Session, plan_id: str) -> Plan:
    plan = get_plan_with_details(db, plan_id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    return plan


def _require_plan_member(plan: Plan, user_id: str) -> None:
    if not is_plan_member(plan, user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not a member of this plan")


def _require_plan_host(plan: Plan, user_id: str) -> None:
    if plan.host_user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the host can do that")


def _users_are_friends(db: Session, user_a: str, user_b: str) -> bool:
    friendship = db.scalar(
        select(Friendship).where(
            Friendship.status == FriendshipStatus.accepted,
            or_(
                and_(Friendship.requester_user_id == user_a, Friendship.addressee_user_id == user_b),
                and_(Friendship.requester_user_id == user_b, Friendship.addressee_user_id == user_a),
            ),
        )
    )
    return friendship is not None


@router.post("/plans", response_model=PlanOut)
def create_plan(
    payload: PlanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PlanOut:
    plan = Plan(
        host_user_id=current_user.id,
        title=payload.title.strip(),
        description=payload.description.strip() if payload.description else None,
        visibility=payload.visibility,
        status=PlanStatus.active,
    )
    db.add(plan)
    db.flush()

    db.add(
        PlanMember(
            plan_id=plan.id,
            user_id=current_user.id,
            role=PlanMemberRole.host,
        )
    )

    for user_id in sorted(set(payload.invited_user_ids)):
        if user_id == current_user.id:
            continue
        invitee = db.get(User, user_id)
        if not invitee:
            continue
        if not _users_are_friends(db, current_user.id, user_id):
            continue
        db.add(
            PlanMember(
                plan_id=plan.id,
                user_id=user_id,
                role=PlanMemberRole.collaborator,
            )
        )

    db.commit()
    return serialize_plan(_get_plan_or_404(db, plan.id), current_user_id=current_user.id)


@router.get("/plans", response_model=list[PlanSummaryOut])
def get_plans(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[PlanSummaryOut]:
    plan_ids = list(
        db.scalars(
            select(PlanMember.plan_id)
            .where(PlanMember.user_id == current_user.id)
        ).all()
    )
    plans = [_get_plan_or_404(db, plan_id) for plan_id in plan_ids]
    plans.sort(key=lambda plan: plan.updated_at, reverse=True)
    return [serialize_plan_summary(plan, current_user_id=current_user.id) for plan in plans]


@router.get("/plans/{plan_id}", response_model=PlanOut)
def get_plan(
    plan_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PlanOut:
    plan = _get_plan_or_404(db, plan_id)
    _require_plan_member(plan, current_user.id)
    return serialize_plan(plan, current_user_id=current_user.id)


@router.put("/plans/{plan_id}", response_model=PlanOut)
def update_plan(
    plan_id: str,
    payload: PlanUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PlanOut:
    plan = _get_plan_or_404(db, plan_id)
    _require_plan_host(plan, current_user.id)

    if payload.title is not None:
        plan.title = payload.title.strip()
    if payload.description is not None:
        plan.description = payload.description.strip() or None
    if payload.visibility is not None:
        plan.visibility = payload.visibility
    if payload.status is not None:
        plan.status = payload.status

    db.add(plan)
    db.commit()
    return serialize_plan(_get_plan_or_404(db, plan_id), current_user_id=current_user.id)


@router.delete("/plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_plan(
    plan_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    plan = _get_plan_or_404(db, plan_id)
    _require_plan_host(plan, current_user.id)
    db.delete(plan)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/plans/{plan_id}/invite", response_model=PlanOut)
def invite_plan_member(
    plan_id: str,
    payload: PlanInviteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PlanOut:
    plan = _get_plan_or_404(db, plan_id)
    _require_plan_host(plan, current_user.id)

    user = db.get(User, payload.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not _users_are_friends(db, current_user.id, payload.user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only invite friends")
    if get_member(plan, payload.user_id):
        return serialize_plan(plan, current_user_id=current_user.id)

    db.add(
        PlanMember(
            plan_id=plan.id,
            user_id=payload.user_id,
            role=PlanMemberRole.collaborator,
        )
    )
    db.commit()
    return serialize_plan(_get_plan_or_404(db, plan_id), current_user_id=current_user.id)


@router.get("/plans/{plan_id}/members", response_model=list[PlanMemberOut])
def get_plan_members(
    plan_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[PlanMemberOut]:
    plan = _get_plan_or_404(db, plan_id)
    _require_plan_member(plan, current_user.id)
    return [serialize_member(member) for member in sorted(plan.members, key=lambda member: member.joined_at)]


@router.delete("/plans/{plan_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_plan_member(
    plan_id: str,
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    plan = _get_plan_or_404(db, plan_id)
    _require_plan_host(plan, current_user.id)
    if user_id == plan.host_user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Host cannot be removed")

    member = db.scalar(
        select(PlanMember).where(PlanMember.plan_id == plan_id, PlanMember.user_id == user_id)
    )
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan member not found")

    db.delete(member)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/plans/{plan_id}/items", response_model=PlanOut)
def add_plan_item(
    plan_id: str,
    payload: PlanItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PlanOut:
    plan = _get_plan_or_404(db, plan_id)
    _require_plan_member(plan, current_user.id)

    place = db.get(Place, payload.place_id)
    if not place:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Place not found")

    existing = db.scalar(
        select(PlanItem).where(PlanItem.plan_id == plan_id, PlanItem.place_id == payload.place_id)
    )
    if existing:
        return serialize_plan(plan, current_user_id=current_user.id)

    db.add(
        PlanItem(
            plan_id=plan_id,
            place_id=payload.place_id,
            added_by_user_id=current_user.id,
            notes=payload.notes.strip() if payload.notes else None,
        )
    )
    db.commit()
    return serialize_plan(_get_plan_or_404(db, plan_id), current_user_id=current_user.id)


@router.get("/plans/{plan_id}/items", response_model=list[PlanItemOut])
def get_plan_items(
    plan_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[PlanItemOut]:
    plan = _get_plan_or_404(db, plan_id)
    _require_plan_member(plan, current_user.id)
    return [serialize_item(item, current_user_id=current_user.id) for item in sorted(plan.items, key=lambda item: item.created_at)]


@router.delete("/plans/{plan_id}/items/{plan_item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_plan_item(
    plan_id: str,
    plan_item_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    plan = _get_plan_or_404(db, plan_id)
    _require_plan_host(plan, current_user.id)

    item = db.scalar(select(PlanItem).where(PlanItem.id == plan_item_id, PlanItem.plan_id == plan_id))
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan item not found")

    if plan.final_place_id == item.place_id:
        plan.final_place_id = None
        plan.status = PlanStatus.active
        db.add(plan)

    db.delete(item)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _upsert_vote(
    plan_item_id: str,
    payload: PlanVoteCreate,
    db: Session,
    current_user: User,
) -> PlanItemOut:
    item = db.get(PlanItem, plan_item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan item not found")

    plan = _get_plan_or_404(db, item.plan_id)
    _require_plan_member(plan, current_user.id)

    existing_vote = db.scalar(
        select(PlanItemVote).where(
            PlanItemVote.plan_item_id == plan_item_id,
            PlanItemVote.user_id == current_user.id,
        )
    )
    if existing_vote:
        existing_vote.vote = payload.vote
        db.add(existing_vote)
    else:
        db.add(
            PlanItemVote(
                plan_item_id=plan_item_id,
                user_id=current_user.id,
                vote=payload.vote,
            )
        )
    db.commit()

    refreshed = _get_plan_or_404(db, item.plan_id)
    refreshed_item = next((candidate for candidate in refreshed.items if candidate.id == plan_item_id), None)
    if not refreshed_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan item not found")
    return serialize_item(refreshed_item, current_user_id=current_user.id)


@router.post("/plans/items/{plan_item_id}/vote", response_model=PlanItemOut)
def create_plan_vote(
    plan_item_id: str,
    payload: PlanVoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PlanItemOut:
    return _upsert_vote(plan_item_id, payload, db, current_user)


@router.put("/plans/items/{plan_item_id}/vote", response_model=PlanItemOut)
def update_plan_vote(
    plan_item_id: str,
    payload: PlanVoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PlanItemOut:
    return _upsert_vote(plan_item_id, payload, db, current_user)


@router.get("/plans/{plan_id}/votes-summary", response_model=PlanVotesSummaryOut)
def get_votes_summary(
    plan_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PlanVotesSummaryOut:
    plan = _get_plan_or_404(db, plan_id)
    _require_plan_member(plan, current_user.id)
    return serialize_votes_summary(plan, current_user_id=current_user.id)


@router.post("/plans/{plan_id}/finalize", response_model=FinalChoiceOut)
def finalize_plan(
    plan_id: str,
    payload: PlanFinalizeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FinalChoiceOut:
    plan = _get_plan_or_404(db, plan_id)
    _require_plan_host(plan, current_user.id)

    chosen_item = None
    if payload.plan_item_id:
        chosen_item = next((item for item in plan.items if item.id == payload.plan_item_id), None)
        if not chosen_item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan item not found")
    else:
        summary = serialize_votes_summary(plan, current_user_id=current_user.id)
        chosen_item = summary.leading_choice

    if not chosen_item:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Add at least one plan item before finalizing")

    plan.final_place_id = chosen_item.place_id
    plan.status = PlanStatus.finalized
    db.add(plan)
    db.commit()
    return serialize_final_choice(_get_plan_or_404(db, plan_id), current_user_id=current_user.id)


@router.get("/plans/{plan_id}/final-choice", response_model=FinalChoiceOut)
def get_final_choice(
    plan_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FinalChoiceOut:
    plan = _get_plan_or_404(db, plan_id)
    _require_plan_member(plan, current_user.id)
    return serialize_final_choice(plan, current_user_id=current_user.id)
