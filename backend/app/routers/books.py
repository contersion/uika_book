from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import CurrentUser
from app.schemas.book import (
    BookDetail,
    BookMetadataUpdate,
    BookRead,
    BookReparseRequest,
    BookReparseResponse,
    BookShelfItem,
)
from app.schemas.book_chapter import BookChapterContent, BookChapterRead, BookChapterSummary
from app.schemas.book_group import BookGroupAssignmentUpdate, BookGroupSummary
from app.schemas.reading_progress import ReadingProgressRead, ReadingProgressSyncRequest
from app.services.book_groups import BookGroupError
from app.services.books import (
    BookChapterNotFoundError,
    BookCoverError,
    BookDeleteError,
    BookNotFoundError,
    BookReadError,
    BookReparseError,
    BookUploadError,
    create_uploaded_book,
    delete_user_book,
    delete_user_book_cover,
    get_user_book_chapter,
    get_user_book_detail,
    list_user_book_chapters,
    list_user_book_groups,
    list_user_books,
    read_book_chapter_content,
    reparse_user_book,
    update_user_book_groups,
    update_user_book_metadata,
    upload_user_book_cover,
)
from app.services.reading_progress import ReadingProgressNotFoundError, get_user_reading_progress, upsert_user_reading_progress


router = APIRouter(prefix="/api/books", tags=["books"])


@router.post("/upload", response_model=BookRead, status_code=status.HTTP_201_CREATED)
async def upload_book(
    current_user: CurrentUser,
    db: Session = Depends(get_db),
    file: UploadFile = File(...),
    chapter_rule_id: int | None = Form(default=None),
) -> BookRead:
    try:
        raw_bytes = await file.read()
        book = create_uploaded_book(
            db=db,
            user=current_user,
            filename=file.filename or "uploaded.txt",
            raw_bytes=raw_bytes,
            chapter_rule_id=chapter_rule_id,
        )
    except BookUploadError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    finally:
        await file.close()

    return BookRead.model_validate(book)


@router.get("", response_model=list[BookShelfItem])
def get_books(
    current_user: CurrentUser,
    db: Session = Depends(get_db),
    search: str | None = Query(default=None),
    group_id: int | None = Query(default=None, ge=1),
    sort: str = Query(default="created_at"),
) -> list[BookShelfItem]:
    items = list_user_books(db, current_user.id, search=search, group_id=group_id, sort=sort)
    return [BookShelfItem.model_validate(item) for item in items]


@router.get("/{book_id}", response_model=BookDetail)
def get_book(book_id: int, current_user: CurrentUser, db: Session = Depends(get_db)) -> BookDetail:
    try:
        book = get_user_book_detail(db, current_user.id, book_id)
    except BookNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return BookDetail.model_validate(book)


def _update_book_metadata_response(
    book_id: int,
    payload: BookMetadataUpdate,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> BookDetail:
    try:
        book = update_user_book_metadata(
            db,
            current_user.id,
            book_id,
            title=payload.title,
            author=payload.author,
            description=payload.description,
            fields_to_update=set(payload.model_fields_set),
        )
    except BookNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except BookUploadError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return BookDetail.model_validate(book)


@router.put("/{book_id}", response_model=BookDetail)
def put_book(
    book_id: int,
    payload: BookMetadataUpdate,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> BookDetail:
    return _update_book_metadata_response(book_id, payload, current_user, db)


@router.patch("/{book_id}", response_model=BookDetail)
def patch_book(
    book_id: int,
    payload: BookMetadataUpdate,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> BookDetail:
    return _update_book_metadata_response(book_id, payload, current_user, db)


@router.post("/{book_id}/cover", response_model=BookDetail)
async def post_book_cover(
    book_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
    file: UploadFile = File(...),
) -> BookDetail:
    try:
        raw_bytes = await file.read()
        book = upload_user_book_cover(
            db,
            current_user.id,
            book_id,
            filename=file.filename or "cover",
            raw_bytes=raw_bytes,
            content_type=file.content_type,
        )
    except BookNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except BookCoverError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    finally:
        await file.close()

    return BookDetail.model_validate(book)


@router.delete("/{book_id}/cover", status_code=status.HTTP_204_NO_CONTENT)
def delete_book_cover(book_id: int, current_user: CurrentUser, db: Session = Depends(get_db)) -> Response:
    try:
        delete_user_book_cover(db, current_user.id, book_id)
    except BookNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except BookCoverError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{book_id}/groups", response_model=list[BookGroupSummary])
def get_book_groups(book_id: int, current_user: CurrentUser, db: Session = Depends(get_db)) -> list[BookGroupSummary]:
    try:
        groups = list_user_book_groups(db, current_user.id, book_id)
    except BookNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return [BookGroupSummary.model_validate(group) for group in groups]


@router.put("/{book_id}/groups", response_model=list[BookGroupSummary])
def put_book_groups(
    book_id: int,
    payload: BookGroupAssignmentUpdate,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> list[BookGroupSummary]:
    try:
        groups = update_user_book_groups(db, current_user.id, book_id, payload.group_ids)
    except BookNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except BookGroupError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return [BookGroupSummary.model_validate(group) for group in groups]


@router.post("/{book_id}/reparse", response_model=BookReparseResponse)
def reparse_book(
    book_id: int,
    payload: BookReparseRequest,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> BookReparseResponse:
    try:
        book, chapters = reparse_user_book(db, current_user.id, book_id, payload.chapter_rule_id)
    except BookNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (BookReadError, BookReparseError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return BookReparseResponse.model_validate(
        {
            "book_id": book.id,
            "chapter_rule_id": book.chapter_rule_id,
            "total_chapters": book.total_chapters,
            "chapters": [BookChapterSummary.model_validate(chapter) for chapter in chapters],
        }
    )


@router.get("/{book_id}/progress", response_model=ReadingProgressRead)
def get_book_progress(book_id: int, current_user: CurrentUser, db: Session = Depends(get_db)) -> ReadingProgressRead:
    try:
        progress = get_user_reading_progress(db, current_user.id, book_id)
    except (BookNotFoundError, ReadingProgressNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return ReadingProgressRead.model_validate(progress)


@router.put("/{book_id}/progress", response_model=ReadingProgressRead)
def put_book_progress(
    book_id: int,
    payload: ReadingProgressSyncRequest,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> ReadingProgressRead:
    try:
        progress = upsert_user_reading_progress(db, current_user.id, book_id, payload)
    except BookNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return ReadingProgressRead.model_validate(progress)


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(book_id: int, current_user: CurrentUser, db: Session = Depends(get_db)) -> Response:
    try:
        delete_user_book(db, current_user.id, book_id)
    except BookNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except BookDeleteError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{book_id}/chapters", response_model=list[BookChapterRead])
def get_book_chapters(book_id: int, current_user: CurrentUser, db: Session = Depends(get_db)) -> list[BookChapterRead]:
    try:
        chapters = list_user_book_chapters(db, current_user.id, book_id)
    except BookNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return [BookChapterRead.model_validate(chapter) for chapter in chapters]


@router.get("/{book_id}/chapters/{chapter_index}", response_model=BookChapterContent)
def get_book_chapter(
    book_id: int,
    chapter_index: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> BookChapterContent:
    try:
        book, chapter = get_user_book_chapter(db, current_user.id, book_id, chapter_index)
        content = read_book_chapter_content(book, chapter)
    except (BookNotFoundError, BookChapterNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except BookReadError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return BookChapterContent.model_validate(
        {
            "book_id": book.id,
            "chapter_index": chapter.chapter_index,
            "chapter_title": chapter.chapter_title,
            "start_offset": chapter.start_offset,
            "end_offset": chapter.end_offset,
            "content": content,
        }
    )
