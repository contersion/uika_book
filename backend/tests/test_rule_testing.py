from contextlib import contextmanager

from fastapi.testclient import TestClient

from app.core import database
from app.core.config import settings
from app.main import create_application
from app.models import Book, ChapterRule, User


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


def create_test_book(tmp_path, user_id: int, text: str, encoding: str = "utf-8") -> int:
    book_path = tmp_path / "sample-book.txt"
    book_path.write_text(text, encoding=encoding)

    session = database.create_session()
    try:
        book = Book(
            user_id=user_id,
            title="Sample Book",
            file_name=book_path.name,
            file_path=str(book_path),
            encoding=encoding,
        )
        session.add(book)
        session.commit()
        session.refresh(book)
        return book.id
    finally:
        session.close()


def get_builtin_full_text_rule() -> ChapterRule:
    session = database.create_session()
    try:
        return session.query(ChapterRule).filter(ChapterRule.rule_name == "单章节全文模式").one()
    finally:
        session.close()


def test_rule_test_endpoint_supports_text_input(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        response = client.post(
            "/api/chapter-rules/test",
            json={
                "text": "序章\n第1章 开始\n正文\n第2章 继续",
                "regex_pattern": "^第\\d+章.*$",
                "flags": "m",
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["matched"] is True
    assert payload["count"] == 2
    assert payload["items"][0]["text"] == "第1章 开始"


def test_rule_test_endpoint_supports_book_input(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        user_id = get_admin_user_id()
        book_id = create_test_book(tmp_path, user_id, "Chapter 1\nHello\nChapter 2\nWorld")

        response = client.post(
            "/api/chapter-rules/test",
            json={
                "book_id": book_id,
                "regex_pattern": "^Chapter\\s+\\d+.*$",
                "flags": "im",
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["matched"] is True
    assert payload["count"] == 2
    assert payload["items"][1]["text"] == "Chapter 2"


def test_rule_test_endpoint_rejects_invalid_regex(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        response = client.post(
            "/api/chapter-rules/test",
            json={
                "text": "第1章 开始",
                "regex_pattern": r"(",
                "flags": "m",
            },
        )

    assert response.status_code == 400
    assert response.json()["detail"].startswith("Invalid regex pattern")


def test_rule_test_endpoint_rejects_invalid_flags(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        response = client.post(
            "/api/chapter-rules/test",
            json={
                "text": "第1章 开始",
                "regex_pattern": "^第\\d+章.*$",
                "flags": "z",
            },
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid regex flags: z"


def test_rule_test_endpoint_handles_full_text_mode(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        full_text_rule = get_builtin_full_text_rule()
        response = client.post(
            "/api/chapter-rules/test",
            json={
                "text": "整本书正文",
                "regex_pattern": full_text_rule.regex_pattern,
                "flags": full_text_rule.flags,
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["matched"] is True
    assert payload["count"] == 1
    assert payload["items"][0]["start"] == 0
    assert payload["items"][0]["end"] == len("整本书正文")


def test_rule_test_endpoint_requires_text_or_book(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        response = client.post(
            "/api/chapter-rules/test",
            json={
                "regex_pattern": "^第\\d+章.*$",
                "flags": "m",
            },
        )

    assert response.status_code == 422
