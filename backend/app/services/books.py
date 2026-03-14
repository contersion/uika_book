import re
from pathlib import Path
import uuid
from types import SimpleNamespace

from sqlalchemy import and_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.models import Book, BookChapter, ChapterRule, ReadingProgress, User
from app.services.book_chapters import replace_book_chapters, save_book_chapters
from app.services.chapter_rules import get_default_rule, get_visible_rule
from app.services.chapter_splitter import ChapterSegment, split_book_into_chapters
from app.utils.encoding import EncodingDetectionError, detect_text_encoding
from app.utils.regex import FULL_TEXT_FLAG, FULL_TEXT_PATTERN, RegexRuleError


class BookAccessError(ValueError):
    pass


class BookNotFoundError(BookAccessError):
    pass


class BookChapterNotFoundError(BookAccessError):
    pass


class BookReadError(BookAccessError):
    pass


class BookUploadError(BookAccessError):
    pass


class BookDeleteError(BookAccessError):
    pass


class BookReparseError(BookAccessError):
    pass


def list_user_books(db: Session, user_id: int, search: str | None = None) -> list[dict[str, object]]:
    statement = (
        select(Book, ReadingProgress)
        .outerjoin(
            ReadingProgress,
            and_(ReadingProgress.book_id == Book.id, ReadingProgress.user_id == user_id),
        )
        .where(Book.user_id == user_id)
        .order_by(Book.updated_at.desc())
    )
    if search and search.strip():
        statement = statement.where(Book.title.contains(search.strip()))

    rows = db.execute(statement).all()
    return [
        {
            "id": book.id,
            "title": book.title,
            "author": book.author,
            "total_chapters": book.total_chapters,
            "total_words": book.total_words,
            "last_read_at": progress.updated_at if progress is not None else None,
            "progress_percent": progress.percent if progress is not None else None,
            "created_at": book.created_at,
            "updated_at": book.updated_at,
        }
        for book, progress in rows
    ]


def get_user_book(db: Session, user_id: int, book_id: int) -> Book:
    statement = select(Book).where(Book.id == book_id, Book.user_id == user_id)
    book = db.execute(statement).scalar_one_or_none()
    if book is None:
        raise BookNotFoundError("Book not found")
    return book


def get_user_book_detail(db: Session, user_id: int, book_id: int) -> Book:
    statement = (
        select(Book)
        .options(selectinload(Book.chapter_rule))
        .where(Book.id == book_id, Book.user_id == user_id)
    )
    book = db.execute(statement).scalar_one_or_none()
    if book is None:
        raise BookNotFoundError("Book not found")
    return book


def list_user_book_chapters(db: Session, user_id: int, book_id: int) -> list[BookChapter]:
    book = get_user_book(db, user_id, book_id)
    statement = (
        select(BookChapter)
        .where(BookChapter.book_id == book.id)
        .order_by(BookChapter.chapter_index.asc())
    )
    return list(db.execute(statement).scalars().all())


def get_user_book_chapter(db: Session, user_id: int, book_id: int, chapter_index: int) -> tuple[Book, BookChapter]:
    book = get_user_book(db, user_id, book_id)
    statement = select(BookChapter).where(
        BookChapter.book_id == book.id,
        BookChapter.chapter_index == chapter_index,
    )
    chapter = db.execute(statement).scalar_one_or_none()
    if chapter is None:
        raise BookChapterNotFoundError("Chapter not found")
    return book, chapter


def read_book_text(book: Book) -> str:
    try:
        return Path(book.file_path).read_text(encoding=book.encoding)
    except FileNotFoundError as exc:
        raise BookReadError("Book file not found") from exc
    except UnicodeDecodeError as exc:
        raise BookReadError("Failed to decode book file with stored encoding") from exc
    except OSError as exc:
        raise BookReadError(f"Failed to read book file: {exc}") from exc


def read_book_chapter_content(book: Book, chapter: BookChapter) -> str:
    text = read_book_text(book)
    text_length = len(text)
    start_offset = max(0, min(chapter.start_offset, text_length))
    end_offset = max(start_offset, min(chapter.end_offset, text_length))
    return text[start_offset:end_offset]


def delete_user_book(db: Session, user_id: int, book_id: int) -> None:
    book = get_user_book(db, user_id, book_id)
    file_paths = _collect_book_file_paths(book)

    try:
        db.delete(book)
        db.flush()
        for file_path in file_paths:
            if file_path.exists():
                file_path.unlink()
        db.commit()
    except OSError as exc:
        db.rollback()
        raise BookDeleteError(f"Failed to delete local book file: {exc}") from exc
    except IntegrityError as exc:
        db.rollback()
        raise BookDeleteError("Failed to delete book") from exc


def reparse_user_book(db: Session, user_id: int, book_id: int, chapter_rule_id: int) -> tuple[Book, list[BookChapter]]:
    book = get_user_book(db, user_id, book_id)
    chapter_rule = get_visible_rule(db, user_id, chapter_rule_id)
    if chapter_rule is None:
        raise BookReparseError("Chapter rule not found")

    try:
        text = read_book_text(book)
        chapter_segments = _split_book_content(text, chapter_rule)
    except RegexRuleError as exc:
        raise BookReparseError(f"Failed to parse chapters: {exc}") from exc

    try:
        book.chapter_rule_id = chapter_rule.id
        book.total_words = _count_text_units(text)
        replace_book_chapters(db, book, chapter_segments)
        db.commit()
        db.refresh(book)
    except IntegrityError as exc:
        db.rollback()
        raise BookReparseError("Failed to reparse book chapters") from exc

    chapters = list_user_book_chapters(db, user_id, book_id)
    return book, chapters


def create_uploaded_book(
    db: Session,
    user: User,
    filename: str,
    raw_bytes: bytes,
    chapter_rule_id: int | None = None,
) -> Book:
    original_file_name = Path(filename or "uploaded.txt").name
    if not original_file_name.lower().endswith(".txt"):
        raise BookUploadError("Only .txt files are supported")
    if not raw_bytes:
        raise BookUploadError("Uploaded file is empty")

    try:
        _, text = detect_text_encoding(raw_bytes)
    except EncodingDetectionError as exc:
        raise BookUploadError(str(exc)) from exc

    chapter_rule = _resolve_chapter_rule(db, user.id, chapter_rule_id)

    book_uuid = uuid.uuid4().hex
    raw_dir = settings.upload_dir / "raw" / str(user.id)
    normalized_dir = settings.upload_dir / "books" / str(user.id)
    raw_dir.mkdir(parents=True, exist_ok=True)
    normalized_dir.mkdir(parents=True, exist_ok=True)

    sanitized_name = _sanitize_filename(original_file_name)
    raw_path = raw_dir / f"{book_uuid}_{sanitized_name}"
    normalized_path = normalized_dir / f"{book_uuid}.txt"

    raw_path.write_bytes(raw_bytes)
    normalized_path.write_text(text, encoding=settings.default_txt_encoding)

    book = Book(
        user_id=user.id,
        title=_detect_title(text, Path(original_file_name).stem),
        author=None,
        description=None,
        file_name=original_file_name,
        file_path=str(normalized_path),
        encoding=settings.default_txt_encoding,
        total_words=_count_text_units(text),
        total_chapters=0,
        chapter_rule_id=chapter_rule.id if chapter_rule is not None else None,
    )

    try:
        db.add(book)
        db.flush()

        chapter_segments = _split_book_content(text, chapter_rule)
        save_book_chapters(db, book, chapter_segments)

        db.commit()
        db.refresh(book)
        return book
    except RegexRuleError as exc:
        db.rollback()
        raw_path.unlink(missing_ok=True)
        normalized_path.unlink(missing_ok=True)
        raise BookUploadError(f"Failed to parse chapters: {exc}") from exc
    except IntegrityError as exc:
        db.rollback()
        raw_path.unlink(missing_ok=True)
        normalized_path.unlink(missing_ok=True)
        raise BookUploadError("Failed to save uploaded book") from exc


def _resolve_chapter_rule(db: Session, user_id: int, chapter_rule_id: int | None) -> ChapterRule | None:
    if chapter_rule_id is not None:
        chapter_rule = get_visible_rule(db, user_id, chapter_rule_id)
        if chapter_rule is None:
            raise BookUploadError("Chapter rule not found")
        return chapter_rule

    return get_default_rule(db, user_id)


def _split_book_content(text: str, chapter_rule: ChapterRule | None) -> list[ChapterSegment]:
    if chapter_rule is None:
        chapter_rule = SimpleNamespace(regex_pattern=FULL_TEXT_PATTERN, flags=FULL_TEXT_FLAG)
    return split_book_into_chapters(text, chapter_rule)


def _collect_book_file_paths(book: Book) -> list[Path]:
    normalized_path = Path(book.file_path)
    raw_dir = settings.upload_dir / "raw" / str(book.user_id)
    raw_paths = list(raw_dir.glob(f"{normalized_path.stem}_*"))
    return [normalized_path, *raw_paths]


def _sanitize_filename(filename: str) -> str:
    sanitized = re.sub(r"[^A-Za-z0-9._-\u4e00-\u9fff]+", "_", filename).strip("._")
    return sanitized or "uploaded.txt"


def _detect_title(text: str, fallback: str) -> str:
    chapter_pattern = re.compile(r"^\s*(第\s*[0-9零〇一二两三四五六七八九十百千万]+\s*[章节回篇卷]|chapter\s+\d+)", re.IGNORECASE)
    for line in text.splitlines()[:20]:
        candidate = line.strip().strip("\ufeff")
        if not candidate:
            continue
        if len(candidate) > 80:
            continue
        if chapter_pattern.match(candidate):
            continue
        if candidate.lower().startswith(("作者:", "作者：", "author:", "author：")):
            continue
        return candidate.strip("《》") or fallback
    return fallback


def _count_text_units(text: str) -> int:
    return len(re.sub(r"\s+", "", text))
