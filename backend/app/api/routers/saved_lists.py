from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import Place, SavedList, SavedListItem, User
from app.schemas import SavedListCreate, SavedListItemCreate, SavedListOut

router = APIRouter()


@router.post("/saved-lists", response_model=SavedListOut)
def create_saved_list(
    payload: SavedListCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SavedListOut:
    saved_list = SavedList(user_id=current_user.id, name=payload.name)
    db.add(saved_list)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="List name already exists") from exc
    db.refresh(saved_list)
    return SavedListOut.model_validate(saved_list)


@router.post("/saved-lists/{list_id}/items", response_model=SavedListOut)
def add_saved_list_item(
    list_id: str,
    payload: SavedListItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SavedListOut:
    saved_list = db.scalar(
        select(SavedList)
        .where(SavedList.id == list_id, SavedList.user_id == current_user.id)
        .options(selectinload(SavedList.items))
    )
    if not saved_list:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved list not found")

    place = db.get(Place, payload.place_id)
    if not place:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Place not found")

    item = SavedListItem(list_id=list_id, place_id=payload.place_id)
    db.add(item)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()

    saved_list = db.scalar(
        select(SavedList)
        .where(SavedList.id == list_id, SavedList.user_id == current_user.id)
        .options(selectinload(SavedList.items))
    )
    return SavedListOut.model_validate(saved_list)


@router.get("/saved-lists", response_model=list[SavedListOut])
def get_my_saved_lists(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[SavedListOut]:
    lists = list(
        db.scalars(
            select(SavedList)
            .where(SavedList.user_id == current_user.id)
            .options(selectinload(SavedList.items))
            .order_by(SavedList.created_at.desc())
        ).all()
    )
    return [SavedListOut.model_validate(item) for item in lists]
