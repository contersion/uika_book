from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import CurrentUser
from app.schemas.book_group import BookGroupCreate, BookGroupRead, BookGroupUpdate
from app.services.book_groups import (
    BookGroupDeleteConflictError,
    BookGroupError,
    BookGroupNotFoundError,
    create_group,
    delete_group,
    list_groups,
    update_group,
)


router = APIRouter(prefix="/api/book-groups", tags=["book-groups"])


@router.get("", response_model=list[BookGroupRead])
def get_book_groups(current_user: CurrentUser, db: Session = Depends(get_db)) -> list[BookGroupRead]:
    return [BookGroupRead.model_validate(group) for group in list_groups(db, current_user.id)]


@router.post("", response_model=BookGroupRead, status_code=status.HTTP_201_CREATED)
def create_book_group(
    payload: BookGroupCreate,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> BookGroupRead:
    try:
        group = create_group(db, current_user.id, payload.name)
    except BookGroupError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return BookGroupRead.model_validate(group)


@router.put("/{group_id}", response_model=BookGroupRead)
def rename_book_group(
    group_id: int,
    payload: BookGroupUpdate,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> BookGroupRead:
    try:
        group = update_group(db, current_user.id, group_id, payload.name)
    except BookGroupNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except BookGroupError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return BookGroupRead.model_validate(group)


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_book_group(group_id: int, current_user: CurrentUser, db: Session = Depends(get_db)) -> Response:
    try:
        delete_group(db, current_user.id, group_id)
    except BookGroupNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except BookGroupDeleteConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except BookGroupError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)

