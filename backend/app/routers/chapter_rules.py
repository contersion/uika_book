from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import CurrentUser
from app.schemas.chapter_rule import ChapterRuleCreate, ChapterRuleRead, ChapterRuleUpdate
from app.schemas.rule_test import RuleTestRequest, RuleTestResponse
from app.services.books import BookAccessError, BookNotFoundError, get_user_book, read_book_text
from app.services.chapter_rules import (
    BuiltinRuleMutationError,
    ChapterRuleError,
    ChapterRuleNotFoundError,
    create_rule,
    delete_rule,
    list_rules,
    update_rule,
)
from app.utils.regex import RegexRuleError, test_rule_on_text


router = APIRouter(prefix="/api/chapter-rules", tags=["chapter-rules"])


@router.get("", response_model=list[ChapterRuleRead])
def get_chapter_rules(current_user: CurrentUser, db: Session = Depends(get_db)) -> list[ChapterRuleRead]:
    return [ChapterRuleRead.model_validate(rule) for rule in list_rules(db, current_user.id)]


@router.post("", response_model=ChapterRuleRead, status_code=status.HTTP_201_CREATED)
def create_chapter_rule(
    payload: ChapterRuleCreate,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> ChapterRuleRead:
    try:
        rule = create_rule(db, current_user, payload)
    except ChapterRuleError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return ChapterRuleRead.model_validate(rule)


@router.post("/test", response_model=RuleTestResponse)
def test_chapter_rule(
    payload: RuleTestRequest,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> RuleTestResponse:
    try:
        source_text = payload.text
        if source_text is None:
            book = get_user_book(db, current_user.id, payload.book_id)
            source_text = read_book_text(book)
        result = test_rule_on_text(source_text, payload.regex_pattern, payload.flags)
    except BookNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (BookAccessError, ChapterRuleError, RegexRuleError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return RuleTestResponse.model_validate(result)


@router.put("/{rule_id}", response_model=ChapterRuleRead)
def update_chapter_rule(
    rule_id: int,
    payload: ChapterRuleUpdate,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> ChapterRuleRead:
    try:
        rule = update_rule(db, current_user, rule_id, payload)
    except ChapterRuleNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (ChapterRuleError, BuiltinRuleMutationError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return ChapterRuleRead.model_validate(rule)


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chapter_rule(rule_id: int, current_user: CurrentUser, db: Session = Depends(get_db)) -> Response:
    try:
        delete_rule(db, current_user, rule_id)
    except ChapterRuleNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except BuiltinRuleMutationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)
