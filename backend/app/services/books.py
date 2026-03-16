import re
import uuid
from collections.abc import Sequence
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.models import Book, BookChapter, BookGroup, ChapterRule, ReadingProgress, User
from app.services.book_chapters import replace_book_chapters, save_book_chapters
from app.services.book_groups import BookGroupError, ensure_default_group, get_user_groups_by_ids
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


class BookCoverError(BookAccessError):
    pass


BOOK_SORT_CREATED_AT = "created_at"
BOOK_SORT_RECENT_READ = "recent_read"
BOOK_SORT_TITLE = "title"
DEFAULT_BOOK_SORT = BOOK_SORT_CREATED_AT
ALLOWED_BOOK_SORTS = {BOOK_SORT_CREATED_AT, BOOK_SORT_RECENT_READ, BOOK_SORT_TITLE}
COVER_URL_PREFIX = "/media/covers"
ALLOWED_COVER_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_COVER_CONTENT_TYPES = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


def list_user_books(
    db: Session,
    user_id: int,
    search: str | None = None,
    group_id: int | None = None,
    sort: str = DEFAULT_BOOK_SORT,
) -> list[dict[str, object]]:
    statement = (
        select(Book, ReadingProgress)
        .options(selectinload(Book.groups))
        .outerjoin(
            ReadingProgress,
            and_(ReadingProgress.book_id == Book.id, ReadingProgress.user_id == user_id),
        )
        .where(Book.user_id == user_id)
    )
    if group_id is not None:
        statement = statement.join(Book.groups).where(BookGroup.id == group_id, BookGroup.user_id == user_id)
    if search and search.strip():
        statement = statement.where(or_(Book.title.contains(search.strip()), Book.file_name.contains(search.strip())))

    rows = db.execute(_apply_book_sort(statement, sort)).unique().all()
    return [_serialize_bookshelf_item(book, progress) for book, progress in rows]


def get_user_book(db: Session, user_id: int, book_id: int, *, load_groups: bool = False) -> Book:
    statement = select(Book)
    if load_groups:
        statement = statement.options(selectinload(Book.groups))

    statement = statement.where(Book.id == book_id, Book.user_id == user_id)
    book = db.execute(statement).scalar_one_or_none()
    if book is None:
        raise BookNotFoundError("Book not found")
    return book


def get_user_book_detail(db: Session, user_id: int, book_id: int) -> dict[str, object]:
    statement = (
        select(Book, ReadingProgress)
        .options(selectinload(Book.chapter_rule), selectinload(Book.groups))
        .outerjoin(
            ReadingProgress,
            and_(ReadingProgress.book_id == Book.id, ReadingProgress.user_id == user_id),
        )
        .where(Book.id == book_id, Book.user_id == user_id)
    )
    row = db.execute(statement).unique().one_or_none()
    if row is None:
        raise BookNotFoundError("Book not found")
    book, progress = row
    return _serialize_book_detail(book, progress)


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


def list_user_book_groups(db: Session, user_id: int, book_id: int) -> list[BookGroup]:
    book = get_user_book(db, user_id, book_id, load_groups=True)
    return list(book.groups)


def update_user_book_groups(db: Session, user_id: int, book_id: int, group_ids: Sequence[int]) -> list[BookGroup]:
    normalized_group_ids = _normalize_group_ids(group_ids)
    if not normalized_group_ids:
        raise BookGroupError("Book must belong to at least one group")

    book = get_user_book(db, user_id, book_id, load_groups=True)
    groups = get_user_groups_by_ids(db, user_id, normalized_group_ids)
    book.groups = groups

    try:
        db.commit()
        db.refresh(book)
    except IntegrityError as exc:
        db.rollback()
        raise BookGroupError("Failed to update book groups") from exc

    return list(book.groups)


def update_user_book_metadata(
    db: Session,
    user_id: int,
    book_id: int,
    *,
    title: str | None | object = None,
    author: str | None | object = None,
    description: str | None | object = None,
    fields_to_update: set[str] | None = None,
) -> dict[str, object]:
    book = get_user_book(db, user_id, book_id)
    fields_to_update = fields_to_update or set()

    if "title" in fields_to_update:
        normalized_title = _normalize_optional_text(title)
        if normalized_title:
            book.title = normalized_title
    if "author" in fields_to_update:
        book.author = _normalize_optional_text(author)
    if "description" in fields_to_update:
        book.description = _normalize_optional_text(description)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise BookUploadError("Failed to update book metadata") from exc

    return get_user_book_detail(db, user_id, book_id)


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


def upload_user_book_cover(
    db: Session,
    user_id: int,
    book_id: int,
    *,
    filename: str,
    raw_bytes: bytes,
    content_type: str | None,
) -> dict[str, object]:
    if not raw_bytes:
        raise BookCoverError("Uploaded cover is empty")

    book = get_user_book(db, user_id, book_id)
    cover_suffix = _resolve_cover_suffix(filename, content_type)
    cover_dir = settings.upload_dir / "covers" / str(user_id)
    cover_dir.mkdir(parents=True, exist_ok=True)

    previous_cover_path = Path(book.cover_path) if book.cover_path else None
    new_cover_path = cover_dir / f"{book.id}_{uuid.uuid4().hex}{cover_suffix}"

    try:
        new_cover_path.write_bytes(raw_bytes)
    except OSError as exc:
        raise BookCoverError(f"Failed to save uploaded cover: {exc}") from exc

    try:
        book.cover_path = str(new_cover_path)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        new_cover_path.unlink(missing_ok=True)
        raise BookCoverError("Failed to save uploaded cover") from exc

    if previous_cover_path is not None and previous_cover_path != new_cover_path:
        previous_cover_path.unlink(missing_ok=True)

    return get_user_book_detail(db, user_id, book_id)


def delete_user_book_cover(db: Session, user_id: int, book_id: int) -> None:
    book = get_user_book(db, user_id, book_id)
    cover_path = Path(book.cover_path) if book.cover_path else None
    book.cover_path = None

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise BookCoverError("Failed to delete book cover") from exc

    if cover_path is not None:
        cover_path.unlink(missing_ok=True)


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
    default_group = ensure_default_group(db, user.id)

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
        title=_derive_book_title(original_file_name),
        author=None,
        description=None,
        cover_path=None,
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
        book.groups.append(default_group)

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


def get_book_display_title(title: str | None, file_name: str | None = None) -> str:
    if title and title.strip():
        return title.strip()

    stem = Path(file_name or "").stem.strip()
    if stem:
        return stem

    if file_name and file_name.strip():
        return file_name.strip()

    return "uploaded"


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
    cover_paths = [Path(book.cover_path)] if book.cover_path else []
    return [normalized_path, *raw_paths, *cover_paths]


def _sanitize_filename(filename: str) -> str:
    sanitized = re.sub(r"[^A-Za-z0-9._-\u4e00-\u9fff]+", "_", filename).strip("._")
    return sanitized or "uploaded.txt"


def _count_text_units(text: str) -> int:
    return len(re.sub(r"\s+", "", text))


def _normalize_group_ids(group_ids: Sequence[int]) -> list[int]:
    return list(dict.fromkeys(int(group_id) for group_id in group_ids))


def _serialize_book_groups(groups: Sequence[BookGroup]) -> list[dict[str, object]]:
    return [{"id": group.id, "name": group.name} for group in groups]


def _apply_book_sort(statement, sort: str):
    normalized_sort = sort if sort in ALLOWED_BOOK_SORTS else DEFAULT_BOOK_SORT

    if normalized_sort == BOOK_SORT_TITLE:
        return statement.order_by(func.lower(Book.title).asc(), Book.created_at.desc(), Book.id.desc())

    if normalized_sort == BOOK_SORT_RECENT_READ:
        unread_last = case((ReadingProgress.updated_at.is_(None), 1), else_=0)
        return statement.order_by(
            unread_last.asc(),
            ReadingProgress.updated_at.desc(),
            Book.created_at.desc(),
            Book.id.desc(),
        )

    return statement.order_by(Book.created_at.desc(), Book.id.desc())


def _serialize_bookshelf_item(book: Book, progress: ReadingProgress | None) -> dict[str, object]:
    recent_read_at = _ensure_utc_datetime(progress.updated_at) if progress is not None else None
    return {
        "id": book.id,
        "title": get_book_display_title(book.title, book.file_name),
        "author": book.author,
        "total_chapters": book.total_chapters,
        "total_words": book.total_words,
        "last_read_at": recent_read_at,
        "recent_read_at": recent_read_at,
        "progress_percent": progress.percent if progress is not None else None,
        "cover_url": _build_cover_url(book.cover_path),
        "created_at": book.created_at,
        "updated_at": book.updated_at,
        "groups": _serialize_book_groups(book.groups),
    }


def _serialize_book_detail(book: Book, progress: ReadingProgress | None) -> dict[str, object]:
    return {
        "id": book.id,
        "user_id": book.user_id,
        "title": get_book_display_title(book.title, book.file_name),
        "author": book.author,
        "description": book.description,
        "encoding": book.encoding,
        "total_words": book.total_words,
        "total_chapters": book.total_chapters,
        "chapter_rule_id": book.chapter_rule_id,
        "file_name": book.file_name,
        "file_path": book.file_path,
        "cover_url": _build_cover_url(book.cover_path),
        "created_at": book.created_at,
        "updated_at": book.updated_at,
        "recent_read_at": _ensure_utc_datetime(progress.updated_at) if progress is not None else None,
        "progress_percent": progress.percent if progress is not None else None,
        "groups": _serialize_book_groups(book.groups),
        "chapter_rule": book.chapter_rule,
    }


def _normalize_optional_text(value: str | None | object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


def _derive_book_title(file_name: str) -> str:
    stem = Path(file_name or "").stem.strip()
    return stem or "uploaded"


def _resolve_cover_suffix(filename: str, content_type: str | None) -> str:
    normalized_content_type = (content_type or "").strip().lower()
    if normalized_content_type in ALLOWED_COVER_CONTENT_TYPES:
        return ALLOWED_COVER_CONTENT_TYPES[normalized_content_type]

    suffix = Path(filename or "").suffix.lower()
    if suffix in ALLOWED_COVER_SUFFIXES:
        return suffix

    raise BookCoverError("Only jpg, jpeg, png, and webp cover images are supported")


def _build_cover_url(cover_path: str | None) -> str | None:
    if not cover_path:
        return None

    cover_root = (settings.upload_dir / "covers").resolve()
    absolute_cover_path = Path(cover_path).resolve()
    try:
        relative_path = absolute_cover_path.relative_to(cover_root).as_posix()
    except ValueError:
        return None
    return f"{COVER_URL_PREFIX}/{relative_path}"


def _ensure_utc_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
