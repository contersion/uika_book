from datetime import datetime, timezone

from sqlalchemy import inspect

from app.core import database
from app.core.config import settings
from app.init_data import init_db
from app.models import Book, BookChapter, ChapterRule, ReadingProgress, User
from app.schemas import BookRead, ChapterRuleCreate, ReadingProgressUpdate, UserCreate


EXPECTED_TABLES = {
    "users",
    "books",
    "book_chapters",
    "reading_progress",
    "chapter_rules",
}


def test_model_metadata_defines_expected_tables():
    assert EXPECTED_TABLES.issubset(database.Base.metadata.tables.keys())


def test_model_relationships_link_expected_entities():
    user = User(username="alice", password_hash="hashed")
    rule = ChapterRule(rule_name="Default Rule", regex_pattern=r"^Chapter\\s+\\d+", flags="MULTILINE")
    book = Book(
        title="Sample Book",
        file_name="sample.txt",
        file_path="/tmp/sample.txt",
        encoding="utf-8",
    )
    chapter = BookChapter(chapter_index=1, chapter_title="Chapter 1", start_offset=0, end_offset=120)
    progress = ReadingProgress(chapter_index=1, char_offset=25, percent=12.5)

    user.books.append(book)
    user.chapter_rules.append(rule)
    book.chapter_rule = rule
    book.chapters.append(chapter)
    user.reading_progresses.append(progress)
    book.reading_progresses.append(progress)

    assert book.user is user
    assert chapter.book is book
    assert progress.user is user
    assert progress.book is book
    assert book.chapter_rule is rule


def test_schemas_support_create_and_read_models():
    create_payload = UserCreate(username="alice", password="secret123")
    rule_payload = ChapterRuleCreate(rule_name="Builtin", regex_pattern=r"^Chapter.+", flags="MULTILINE")
    progress_payload = ReadingProgressUpdate(chapter_index=3, char_offset=42, percent=37.5)
    now = datetime.now(timezone.utc)

    book_model = Book(
        id=1,
        user_id=2,
        title="Schema Book",
        author="Author",
        description="Desc",
        file_name="schema.txt",
        file_path="/tmp/schema.txt",
        encoding="utf-8",
        total_words=1234,
        total_chapters=10,
        chapter_rule_id=None,
        created_at=now,
        updated_at=now,
    )

    book_read = BookRead.model_validate(book_model)

    assert create_payload.username == "alice"
    assert rule_payload.regex_pattern == r"^Chapter.+"
    assert progress_payload.chapter_index == 3
    assert book_read.title == "Schema Book"
    assert book_read.user_id == 2


def test_init_db_creates_all_application_tables(monkeypatch, tmp_path):
    db_path = tmp_path / "reader.db"
    data_dir = tmp_path / "data"
    upload_dir = tmp_path / "uploads"

    monkeypatch.setattr(settings, "data_dir", data_dir)
    monkeypatch.setattr(settings, "upload_dir", upload_dir)
    monkeypatch.setattr(settings, "database_url", f"sqlite:///{db_path.as_posix()}")
    monkeypatch.setattr(database, "engine", database.build_engine(settings.database_url))

    init_db()

    inspector = inspect(database.engine)
    assert EXPECTED_TABLES.issubset(set(inspector.get_table_names()))
