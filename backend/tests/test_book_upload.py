from contextlib import contextmanager
from pathlib import Path

from fastapi.testclient import TestClient

from app.core import database
from app.core.config import settings
from app.main import create_application
from app.models import Book, BookChapter, ChapterRule, User
from app.utils.encoding import detect_text_encoding


TEXT_WITH_TWO_CHAPTERS = "\u4e09\u4f53\n\n\u7b2c1\u7ae0 \u5f00\u59cb\n\u5185\u5bb9\n\u7b2c2\u7ae0 \u7ee7\u7eed\n\u66f4\u591a"
TEXT_WITH_ONE_MATCH = "\u6211\u7684\u5c0f\u8bf4\n\u7b2c1\u7ae0 \u5f00\u59cb"
TEXT_WITHOUT_CHAPTERS = "\u6211\u7684\u5c0f\u8bf4\n\u8fd9\u662f\u6b63\u6587\u5185\u5bb9"


@contextmanager
def authenticated_client(monkeypatch, tmp_path):
    db_path = tmp_path / "reader.db"
    data_dir = tmp_path / "data"
    upload_dir = tmp_path / "uploads"

    monkeypatch.setattr(settings, "data_dir", data_dir)
    monkeypatch.setattr(settings, "upload_dir", upload_dir)
    monkeypatch.setattr(settings, "database_url", f"sqlite:///{db_path.as_posix()}")
    monkeypatch.setattr(settings, "default_admin_username", "admin")
    monkeypatch.setattr(settings, "default_admin_password", "admin123")
    monkeypatch.setattr(settings, "secret_key", "test-secret-key")
    monkeypatch.setattr(database, "engine", database.build_engine(settings.database_url))

    with TestClient(create_application()) as client:
        login_response = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "admin123"},
        )
        access_token = login_response.json()["access_token"]
        client.headers.update({"Authorization": f"Bearer {access_token}"})
        yield client


def get_admin_user_id() -> int:
    session = database.create_session()
    try:
        user = session.query(User).filter(User.username == "admin").one()
        return user.id
    finally:
        session.close()


def get_book(book_id: int) -> Book:
    session = database.create_session()
    try:
        return session.query(Book).filter(Book.id == book_id).one()
    finally:
        session.close()


def get_book_chapters(book_id: int) -> list[BookChapter]:
    session = database.create_session()
    try:
        return list(
            session.query(BookChapter)
            .filter(BookChapter.book_id == book_id)
            .order_by(BookChapter.chapter_index.asc())
            .all()
        )
    finally:
        session.close()


def create_invalid_rule(user_id: int) -> ChapterRule:
    session = database.create_session()
    try:
        session.query(ChapterRule).filter(ChapterRule.user_id == user_id).update({"is_default": False})
        rule = ChapterRule(
            user_id=user_id,
            rule_name="broken-rule",
            regex_pattern="(",
            flags="m",
            description="broken",
            is_builtin=False,
            is_default=False,
        )
        session.add(rule)
        session.commit()
        session.refresh(rule)
        return rule
    finally:
        session.close()


def get_default_rule_id(client: TestClient) -> int:
    rules_response = client.get("/api/chapter-rules")
    return next(item["id"] for item in rules_response.json() if item["is_default"])


def test_detect_text_encoding_supports_utf8_gbk_and_utf16():
    utf8_encoding, utf8_text = detect_text_encoding("\u7b2c\u4e00\u7ae0 \u5f00\u59cb".encode("utf-8"))
    gbk_encoding, gbk_text = detect_text_encoding("\u7b2c\u4e00\u7ae0 \u5f00\u59cb".encode("gbk"))
    utf16_encoding, utf16_text = detect_text_encoding("\u7b2c\u4e00\u7ae0 \u5f00\u59cb".encode("utf-16"))

    assert utf8_encoding == "utf-8"
    assert gbk_encoding == "gbk"
    assert utf16_encoding == "utf-16"
    assert utf8_text == gbk_text == utf16_text == "\u7b2c\u4e00\u7ae0 \u5f00\u59cb"


def test_upload_txt_creates_book_saves_files_and_parses_chapters(monkeypatch, tmp_path):
    raw_bytes = TEXT_WITH_TWO_CHAPTERS.encode("utf-8")
    second_start = TEXT_WITH_TWO_CHAPTERS.index("\u7b2c2\u7ae0 \u7ee7\u7eed")

    with authenticated_client(monkeypatch, tmp_path) as client:
        default_rule_id = get_default_rule_id(client)
        response = client.post(
            "/api/books/upload",
            files={"file": ("three-body.txt", raw_bytes, "text/plain")},
        )

    assert response.status_code == 201
    payload = response.json()
    assert payload["title"] == "three-body"
    assert payload["file_name"] == "three-body.txt"
    assert payload["encoding"] == "utf-8"
    assert payload["chapter_rule_id"] == default_rule_id

    book = get_book(payload["id"])
    chapters = get_book_chapters(payload["id"])
    normalized_text = Path(book.file_path).read_text(encoding="utf-8")
    raw_files = list((settings.upload_dir / "raw").rglob("*.txt"))

    assert normalized_text == TEXT_WITH_TWO_CHAPTERS
    assert raw_files
    assert raw_files[0].read_bytes() == raw_bytes
    assert book.total_words == len("".join(TEXT_WITH_TWO_CHAPTERS.split()))
    assert book.total_chapters == 2
    assert [(chapter.chapter_index, chapter.chapter_title) for chapter in chapters] == [
        (0, "\u7b2c1\u7ae0 \u5f00\u59cb"),
        (1, "\u7b2c2\u7ae0 \u7ee7\u7eed"),
    ]
    assert [(chapter.start_offset, chapter.end_offset) for chapter in chapters] == [
        (0, second_start),
        (second_start, len(TEXT_WITH_TWO_CHAPTERS)),
    ]


def test_upload_txt_supports_gbk_and_explicit_chapter_rule(monkeypatch, tmp_path):
    raw_bytes = TEXT_WITH_ONE_MATCH.encode("gbk")

    with authenticated_client(monkeypatch, tmp_path) as client:
        rules_response = client.get("/api/chapter-rules")
        builtin_rule_id = next(item["id"] for item in rules_response.json() if item["rule_name"] == "\u4e2d\u6587\u7ae0\u8282\u89c4\u5219")

        response = client.post(
            "/api/books/upload",
            data={"chapter_rule_id": str(builtin_rule_id)},
            files={"file": ("novel.txt", raw_bytes, "text/plain")},
        )

    assert response.status_code == 201
    payload = response.json()
    assert payload["title"] == "novel"
    assert payload["encoding"] == "utf-8"
    assert payload["chapter_rule_id"] == builtin_rule_id

    book = get_book(payload["id"])
    chapters = get_book_chapters(payload["id"])
    assert book.total_chapters == 1
    assert chapters[0].chapter_title == "\u7b2c1\u7ae0 \u5f00\u59cb"


def test_upload_txt_falls_back_to_full_text_when_no_chapters_match(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        response = client.post(
            "/api/books/upload",
            files={"file": ("plain.txt", TEXT_WITHOUT_CHAPTERS.encode("utf-8"), "text/plain")},
        )

    assert response.status_code == 201
    payload = response.json()

    book = get_book(payload["id"])
    chapters = get_book_chapters(payload["id"])
    assert book.total_chapters == 1
    assert chapters == [
        chapters[0]
    ]
    assert chapters[0].chapter_index == 0
    assert chapters[0].chapter_title == "\u5168\u6587"
    assert chapters[0].start_offset == 0
    assert chapters[0].end_offset == len(TEXT_WITHOUT_CHAPTERS)


def test_upload_txt_returns_friendly_error_when_chapter_parsing_fails(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        user_id = get_admin_user_id()
        invalid_rule = create_invalid_rule(user_id)

        response = client.post(
            "/api/books/upload",
            data={"chapter_rule_id": str(invalid_rule.id)},
            files={"file": ("broken-rule.txt", TEXT_WITH_ONE_MATCH.encode("utf-8"), "text/plain")},
        )

    assert response.status_code == 400
    assert response.json()["detail"].startswith("Failed to parse chapters")


def test_upload_txt_rejects_non_txt_file(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        response = client.post(
            "/api/books/upload",
            files={"file": ("image.jpg", b"fake-image", "image/jpeg")},
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "Only .txt files are supported"


def test_upload_txt_rejects_unknown_encoding(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        response = client.post(
            "/api/books/upload",
            files={"file": ("broken.txt", b"\xff\xfe\xff\xfe\x00\x81", "text/plain")},
        )

    assert response.status_code == 400
    assert response.json()["detail"].startswith("Unable to detect text encoding")
