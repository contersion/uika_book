from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ReadingProgress
from app.schemas.reading_progress import ReadingProgressSyncRequest
from app.services.books import BookNotFoundError, get_user_book


class ReadingProgressNotFoundError(ValueError):
    pass


class ReadingProgressConflictIgnoredError(ValueError):
    pass


def get_user_reading_progress(db: Session, user_id: int, book_id: int) -> ReadingProgress:
    get_user_book(db, user_id, book_id)
    progress = _get_progress_row(db, user_id, book_id)
    if progress is None:
        raise ReadingProgressNotFoundError("Reading progress not found")
    progress.updated_at = _ensure_utc_datetime(progress.updated_at)
    return progress


def upsert_user_reading_progress(
    db: Session,
    user_id: int,
    book_id: int,
    payload: ReadingProgressSyncRequest,
) -> ReadingProgress:
    get_user_book(db, user_id, book_id)
    incoming_updated_at = _ensure_utc_datetime(payload.updated_at)
    progress = _get_progress_row(db, user_id, book_id)

    if progress is None:
        progress = ReadingProgress(
            user_id=user_id,
            book_id=book_id,
            chapter_index=payload.chapter_index,
            char_offset=payload.char_offset,
            percent=payload.percent,
            updated_at=incoming_updated_at,
        )
        db.add(progress)
        db.commit()
        db.refresh(progress)
        progress.updated_at = _ensure_utc_datetime(progress.updated_at)
        return progress

    current_updated_at = _ensure_utc_datetime(progress.updated_at)
    if current_updated_at > incoming_updated_at:
        progress.updated_at = current_updated_at
        return progress

    progress.chapter_index = payload.chapter_index
    progress.char_offset = payload.char_offset
    progress.percent = payload.percent
    progress.updated_at = incoming_updated_at
    db.commit()
    db.refresh(progress)
    progress.updated_at = _ensure_utc_datetime(progress.updated_at)
    return progress


def _get_progress_row(db: Session, user_id: int, book_id: int) -> ReadingProgress | None:
    statement = select(ReadingProgress).where(
        ReadingProgress.user_id == user_id,
        ReadingProgress.book_id == book_id,
    )
    return db.execute(statement).scalar_one_or_none()


def _ensure_utc_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
