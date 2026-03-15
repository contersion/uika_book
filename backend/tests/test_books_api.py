from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from app.core import database
from app.core.config import settings
from app.main import create_application
from app.models import Book, ReadingProgress, User


BOOK_ONE_TEXT = "\u4e09\u4f53\n\n\u7b2c1\u7ae0 \u5f00\u59cb\n\u5185\u5bb9\n\u7b2c2\u7ae0 \u7ee7\u7eed\n\u66f4\u591a"
BOOK_TWO_TEXT = "\u7403\u72b6\u95ea\u7535\n\n\u7b2c1\u7ae0 \u843d\u96f7\n\u6b63\u6587"


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


def upload_book(client: TestClient, file_name: str, text: str) -> dict:
    response = client.post(
        "/api/books/upload",
        files={"file": (file_name, text.encode("utf-8"), "text/plain")},
    )
    assert response.status_code == 201
    return response.json()


def update_book_author(book_id: int, author: str) -> None:
    session = database.create_session()
    try:
        book = session.query(Book).filter(Book.id == book_id).one()
        book.author = author
        session.commit()
    finally:
        session.close()


def create_progress(user_id: int, book_id: int, percent: float) -> None:
    session = database.create_session()
    try:
        session.add(
            ReadingProgress(
                user_id=user_id,
                book_id=book_id,
                chapter_index=1,
                char_offset=12,
                percent=percent,
                updated_at=datetime.now(timezone.utc),
            )
        )
        session.commit()
    finally:
        session.close()


def get_book_or_none(book_id: int) -> Book | None:
    session = database.create_session()
    try:
        return session.query(Book).filter(Book.id == book_id).one_or_none()
    finally:
        session.close()


def test_get_books_returns_bookshelf_and_supports_search(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        user_id = get_admin_user_id()
        first_book = upload_book(client, "book-one.txt", BOOK_ONE_TEXT)
        second_book = upload_book(client, "book-two.txt", BOOK_TWO_TEXT)
        update_book_author(first_book["id"], "Liu Cixin")
        create_progress(user_id, first_book["id"], 37.5)

        response = client.get("/api/books", params={"search": "book-one"})

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["id"] == first_book["id"]
    assert payload[0]["title"] == "book-one"
    assert payload[0]["author"] == "Liu Cixin"
    assert payload[0]["total_chapters"] == 2
    assert payload[0]["total_words"] == len("".join(BOOK_ONE_TEXT.split()))
    assert payload[0]["progress_percent"] == 37.5
    assert payload[0]["last_read_at"] is not None
    assert all(item["id"] != second_book["id"] for item in payload)


def test_get_book_detail_returns_book_and_chapter_rule(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        book = upload_book(client, "detail.txt", BOOK_ONE_TEXT)
        response = client.get(f"/api/books/{book['id']}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == book["id"]
    assert payload["title"] == "detail"
    assert payload["chapter_rule_id"] is not None
    assert payload["chapter_rule"]["id"] == payload["chapter_rule_id"]
    assert payload["chapter_rule"]["rule_name"] == "\u4e2d\u6587\u7ae0\u8282\u89c4\u5219"


def test_get_book_chapters_returns_toc(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        book = upload_book(client, "toc.txt", BOOK_ONE_TEXT)
        response = client.get(f"/api/books/{book['id']}/chapters")

    assert response.status_code == 200
    payload = response.json()
    assert [(item["chapter_index"], item["chapter_title"]) for item in payload] == [
        (0, "\u7b2c1\u7ae0 \u5f00\u59cb"),
        (1, "\u7b2c2\u7ae0 \u7ee7\u7eed"),
    ]


def test_get_book_chapter_returns_single_chapter_content(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        book = upload_book(client, "chapter.txt", BOOK_ONE_TEXT)
        response = client.get(f"/api/books/{book['id']}/chapters/1")

    assert response.status_code == 200
    payload = response.json()
    assert payload["book_id"] == book["id"]
    assert payload["chapter_index"] == 1
    assert payload["chapter_title"] == "\u7b2c2\u7ae0 \u7ee7\u7eed"
    assert payload["content"] == "\u7b2c2\u7ae0 \u7ee7\u7eed\n\u66f4\u591a"
    assert "\u7b2c1\u7ae0 \u5f00\u59cb" not in payload["content"]


def test_delete_book_removes_database_records_and_local_files(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        book = upload_book(client, "delete.txt", BOOK_ONE_TEXT)
        db_book = get_book_or_none(book["id"])
        assert db_book is not None
        normalized_path = Path(db_book.file_path)
        raw_files = list((settings.upload_dir / "raw" / str(db_book.user_id)).glob(f"{normalized_path.stem}_*"))

        response = client.delete(f"/api/books/{book['id']}")

    assert response.status_code == 204
    assert get_book_or_none(book["id"]) is None
    assert not normalized_path.exists()
    assert all(not raw_file.exists() for raw_file in raw_files)
