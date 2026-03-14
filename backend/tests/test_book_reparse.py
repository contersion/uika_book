from contextlib import contextmanager

from fastapi.testclient import TestClient

from app.core import database
from app.core.config import settings
from app.main import create_application
from app.models import Book, BookChapter, ChapterRule, User


BOOK_TEXT = "\u4e09\u4f53\n\n\u7b2c1\u7ae0 \u5f00\u59cb\n\u5185\u5bb9\n\u7b2c2\u7ae0 \u7ee7\u7eed\n\u66f4\u591a"
PLAIN_TEXT = "\u4e09\u4f53\n\u8fd9\u662f\u4e00\u6bb5\u65e0\u76ee\u5f55\u6b63\u6587"


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


def upload_book(client: TestClient, file_name: str, text: str) -> dict:
    response = client.post(
        "/api/books/upload",
        files={"file": (file_name, text.encode("utf-8"), "text/plain")},
    )
    assert response.status_code == 201
    return response.json()


def list_book_chapters(book_id: int) -> list[BookChapter]:
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


def get_book(book_id: int) -> Book:
    session = database.create_session()
    try:
        return session.query(Book).filter(Book.id == book_id).one()
    finally:
        session.close()


def get_admin_user_id() -> int:
    session = database.create_session()
    try:
        return session.query(User).filter(User.username == "admin").one().id
    finally:
        session.close()


def create_invalid_rule(user_id: int) -> ChapterRule:
    session = database.create_session()
    try:
        rule = ChapterRule(
            user_id=user_id,
            rule_name="broken-reparse-rule",
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


def test_reparse_book_replaces_existing_chapters_and_updates_rule(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        book = upload_book(client, "novel.txt", BOOK_TEXT)
        rules_response = client.get("/api/chapter-rules")
        full_text_rule_id = next(item["id"] for item in rules_response.json() if item["rule_name"] == "\u5355\u7ae0\u8282\u5168\u6587\u6a21\u5f0f")

        response = client.post(
            f"/api/books/{book['id']}/reparse",
            json={"chapter_rule_id": full_text_rule_id},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["book_id"] == book["id"]
    assert payload["chapter_rule_id"] == full_text_rule_id
    assert payload["total_chapters"] == 1
    assert payload["chapters"] == [
        {
            "chapter_index": 0,
            "chapter_title": "\u5168\u6587",
            "start_offset": 0,
            "end_offset": len(BOOK_TEXT),
        }
    ]

    db_book = get_book(book["id"])
    db_chapters = list_book_chapters(book["id"])
    assert db_book.chapter_rule_id == full_text_rule_id
    assert db_book.total_chapters == 1
    assert len(db_chapters) == 1
    assert db_chapters[0].chapter_title == "\u5168\u6587"


def test_reparse_book_falls_back_to_full_text_when_rule_matches_nothing(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        book = upload_book(client, "plain.txt", PLAIN_TEXT)
        rules_response = client.get("/api/chapter-rules")
        chinese_rule_id = next(item["id"] for item in rules_response.json() if item["rule_name"] == "\u4e2d\u6587\u7ae0\u8282\u89c4\u5219")

        response = client.post(
            f"/api/books/{book['id']}/reparse",
            json={"chapter_rule_id": chinese_rule_id},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_chapters"] == 1
    assert payload["chapters"][0]["chapter_title"] == "\u5168\u6587"
    assert payload["chapters"][0]["end_offset"] == len(PLAIN_TEXT)


def test_reparse_book_returns_friendly_error_for_invalid_rule(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        book = upload_book(client, "invalid.txt", BOOK_TEXT)
        invalid_rule = create_invalid_rule(get_admin_user_id())

        response = client.post(
            f"/api/books/{book['id']}/reparse",
            json={"chapter_rule_id": invalid_rule.id},
        )

    assert response.status_code == 400
    assert response.json()["detail"].startswith("Failed to parse chapters")
