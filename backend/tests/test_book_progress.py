from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.core import database
from app.core.config import settings
from app.main import create_application
from app.models import ReadingProgress, User


BOOK_TEXT = "\u4e09\u4f53\n\n\u7b2c1\u7ae0 \u5f00\u59cb\n\u5185\u5bb9\n\u7b2c2\u7ae0 \u7ee7\u7eed\n\u66f4\u591a"


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


def get_admin_user_id() -> int:
    session = database.create_session()
    try:
        return session.query(User).filter(User.username == "admin").one().id
    finally:
        session.close()


def get_progress(book_id: int) -> ReadingProgress | None:
    session = database.create_session()
    try:
        user_id = get_admin_user_id()
        return session.query(ReadingProgress).filter(ReadingProgress.user_id == user_id, ReadingProgress.book_id == book_id).one_or_none()
    finally:
        session.close()


def parse_api_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def test_get_book_progress_returns_latest_progress(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        book = upload_book(client, "progress.txt", BOOK_TEXT)
        updated_at = datetime(2026, 3, 14, 9, 30, tzinfo=timezone.utc)
        put_response = client.put(
            f"/api/books/{book['id']}/progress",
            json={
                "chapter_index": 1,
                "char_offset": 18,
                "percent": 42.5,
                "updated_at": updated_at.isoformat(),
            },
        )
        assert put_response.status_code == 200

        response = client.get(f"/api/books/{book['id']}/progress")

    assert response.status_code == 200
    payload = response.json()
    assert payload["book_id"] == book["id"]
    assert payload["chapter_index"] == 1
    assert payload["char_offset"] == 18
    assert payload["percent"] == 42.5
    assert parse_api_datetime(payload["updated_at"]) == updated_at


def test_put_book_progress_creates_or_updates_progress(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        book = upload_book(client, "update.txt", BOOK_TEXT)
        first_time = datetime(2026, 3, 14, 8, 0, tzinfo=timezone.utc)
        second_time = first_time + timedelta(minutes=10)

        first_response = client.put(
            f"/api/books/{book['id']}/progress",
            json={
                "chapter_index": 0,
                "char_offset": 5,
                "percent": 10.0,
                "updated_at": first_time.isoformat(),
            },
        )
        second_response = client.put(
            f"/api/books/{book['id']}/progress",
            json={
                "chapter_index": 1,
                "char_offset": 7,
                "percent": 55.0,
                "updated_at": second_time.isoformat(),
            },
        )

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    payload = second_response.json()
    assert payload["chapter_index"] == 1
    assert payload["char_offset"] == 7
    assert payload["percent"] == 55.0
    assert parse_api_datetime(payload["updated_at"]) == second_time

    db_progress = get_progress(book["id"])
    assert db_progress is not None
    assert db_progress.chapter_index == 1
    assert db_progress.char_offset == 7
    assert db_progress.percent == 55.0


def test_put_book_progress_keeps_newer_record_when_conflict_happens(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        book = upload_book(client, "conflict.txt", BOOK_TEXT)
        newer_time = datetime(2026, 3, 14, 12, 0, tzinfo=timezone.utc)
        older_time = newer_time - timedelta(minutes=30)

        first_response = client.put(
            f"/api/books/{book['id']}/progress",
            json={
                "chapter_index": 1,
                "char_offset": 21,
                "percent": 60.0,
                "updated_at": newer_time.isoformat(),
            },
        )
        second_response = client.put(
            f"/api/books/{book['id']}/progress",
            json={
                "chapter_index": 0,
                "char_offset": 1,
                "percent": 5.0,
                "updated_at": older_time.isoformat(),
            },
        )

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    payload = second_response.json()
    assert payload["chapter_index"] == 1
    assert payload["char_offset"] == 21
    assert payload["percent"] == 60.0
    assert parse_api_datetime(payload["updated_at"]) == newer_time

    db_progress = get_progress(book["id"])
    assert db_progress is not None
    assert db_progress.chapter_index == 1
    assert db_progress.char_offset == 21
    assert db_progress.percent == 60.0
