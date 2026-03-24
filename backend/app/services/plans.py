from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Plan, PlanItem, PlanItemVote, PlanMember, PlanVoteValue
from app.schemas import (
    FinalChoiceOut,
    PlanItemOut,
    PlanItemVoteOut,
    PlanMemberOut,
    PlanOut,
    PlanSummaryOut,
    PlanVotesSummaryOut,
    PlaceOut,
    UserSummary,
    VoteSummaryOut,
)


def plan_load_statement(plan_id: str):
    return (
        select(Plan)
        .where(Plan.id == plan_id)
        .options(
            selectinload(Plan.host),
            selectinload(Plan.final_place),
            selectinload(Plan.members).selectinload(PlanMember.user),
            selectinload(Plan.items).selectinload(PlanItem.place),
            selectinload(Plan.items).selectinload(PlanItem.added_by_user),
            selectinload(Plan.items).selectinload(PlanItem.votes).selectinload(PlanItemVote.user),
        )
    )


def get_plan_with_details(db: Session, plan_id: str) -> Plan | None:
    return db.scalar(plan_load_statement(plan_id))


def is_plan_member(plan: Plan, user_id: str) -> bool:
    return any(member.user_id == user_id for member in plan.members)


def get_member(plan: Plan, user_id: str) -> PlanMember | None:
    return next((member for member in plan.members if member.user_id == user_id), None)


def _vote_sort_key(item: PlanItem) -> tuple[int, int, int]:
    yes_count = sum(1 for vote in item.votes if vote.vote == PlanVoteValue.yes)
    no_count = sum(1 for vote in item.votes if vote.vote == PlanVoteValue.no)
    maybe_count = sum(1 for vote in item.votes if vote.vote == PlanVoteValue.maybe)
    return (yes_count, -no_count, maybe_count)


def compute_leading_item(plan: Plan) -> PlanItem | None:
    if not plan.items:
        return None
    return max(plan.items, key=_vote_sort_key)


def summarize_votes(item: PlanItem, current_user_id: str | None = None) -> VoteSummaryOut:
    yes_count = sum(1 for vote in item.votes if vote.vote == PlanVoteValue.yes)
    no_count = sum(1 for vote in item.votes if vote.vote == PlanVoteValue.no)
    maybe_count = sum(1 for vote in item.votes if vote.vote == PlanVoteValue.maybe)
    current_vote = next(
        (vote.vote for vote in item.votes if current_user_id and vote.user_id == current_user_id),
        None,
    )
    return VoteSummaryOut(
        yes_count=yes_count,
        no_count=no_count,
        maybe_count=maybe_count,
        total_votes=len(item.votes),
        current_user_vote=current_vote,
    )


def serialize_vote(vote: PlanItemVote) -> PlanItemVoteOut:
    return PlanItemVoteOut(
        id=vote.id,
        plan_item_id=vote.plan_item_id,
        user_id=vote.user_id,
        vote=vote.vote,
        created_at=vote.created_at,
        updated_at=vote.updated_at,
        user=UserSummary.model_validate(vote.user),
    )


def serialize_item(item: PlanItem, current_user_id: str | None = None) -> PlanItemOut:
    return PlanItemOut(
        id=item.id,
        plan_id=item.plan_id,
        place_id=item.place_id,
        added_by_user_id=item.added_by_user_id,
        notes=item.notes,
        created_at=item.created_at,
        place=PlaceOut.model_validate(item.place),
        added_by_user=UserSummary.model_validate(item.added_by_user),
        votes=[serialize_vote(vote) for vote in sorted(item.votes, key=lambda vote: vote.created_at)],
        vote_summary=summarize_votes(item, current_user_id=current_user_id),
    )


def serialize_member(member: PlanMember) -> PlanMemberOut:
    return PlanMemberOut(
        plan_id=member.plan_id,
        user_id=member.user_id,
        role=member.role,
        joined_at=member.joined_at,
        user=UserSummary.model_validate(member.user),
    )


def serialize_plan(plan: Plan, current_user_id: str | None = None) -> PlanOut:
    leading_item = compute_leading_item(plan)
    final_item = next((item for item in plan.items if plan.final_place_id and item.place_id == plan.final_place_id), None)
    return PlanOut(
        id=plan.id,
        host_user_id=plan.host_user_id,
        title=plan.title,
        description=plan.description,
        status=plan.status,
        visibility=plan.visibility,
        final_place_id=plan.final_place_id,
        created_at=plan.created_at,
        updated_at=plan.updated_at,
        host=UserSummary.model_validate(plan.host),
        members=[serialize_member(member) for member in sorted(plan.members, key=lambda member: member.joined_at)],
        items=[serialize_item(item, current_user_id=current_user_id) for item in sorted(plan.items, key=lambda item: item.created_at)],
        final_choice=serialize_item(final_item, current_user_id=current_user_id) if final_item else None,
        leading_choice=serialize_item(leading_item, current_user_id=current_user_id) if leading_item else None,
    )


def serialize_plan_summary(plan: Plan, current_user_id: str | None = None) -> PlanSummaryOut:
    leading_item = compute_leading_item(plan)
    final_item = next((item for item in plan.items if plan.final_place_id and item.place_id == plan.final_place_id), None)
    return PlanSummaryOut(
        id=plan.id,
        host_user_id=plan.host_user_id,
        title=plan.title,
        description=plan.description,
        status=plan.status,
        visibility=plan.visibility,
        final_place_id=plan.final_place_id,
        created_at=plan.created_at,
        updated_at=plan.updated_at,
        host=UserSummary.model_validate(plan.host),
        member_count=len(plan.members),
        item_count=len(plan.items),
        final_choice=serialize_item(final_item, current_user_id=current_user_id) if final_item else None,
        leading_choice=serialize_item(leading_item, current_user_id=current_user_id) if leading_item else None,
    )


def serialize_votes_summary(plan: Plan, current_user_id: str | None = None) -> PlanVotesSummaryOut:
    leading_item = compute_leading_item(plan)
    return PlanVotesSummaryOut(
        plan_id=plan.id,
        items=[serialize_item(item, current_user_id=current_user_id) for item in sorted(plan.items, key=lambda item: item.created_at)],
        leading_choice=serialize_item(leading_item, current_user_id=current_user_id) if leading_item else None,
    )


def serialize_final_choice(plan: Plan, current_user_id: str | None = None) -> FinalChoiceOut:
    leading_item = compute_leading_item(plan)
    final_item = next((item for item in plan.items if plan.final_place_id and item.place_id == plan.final_place_id), None)
    return FinalChoiceOut(
        plan_id=plan.id,
        status=plan.status,
        final_choice=serialize_item(final_item, current_user_id=current_user_id) if final_item else None,
        leading_choice=serialize_item(leading_item, current_user_id=current_user_id) if leading_item else None,
    )
