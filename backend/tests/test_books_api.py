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
BOOK_THREE_TEXT = "\u6d41\u6d6a\u5730\u7403\n\n\u7b2c1\u7ae0 \u51fa\u53d1\n\u4e16\u754c"
COVER_PNG_BYTES = b"\x89PNG\r\n\x1a\nfake-cover"


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


def upload_cover(client: TestClient, book_id: int, file_name: str = "cover.png") -> dict:
    response = client.post(
        f"/api/books/{book_id}/cover",
        files={"file": (file_name, COVER_PNG_BYTES, "image/png")},
    )
    assert response.status_code == 200
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


def test_patch_book_updates_display_title_across_detail_and_bookshelf(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        book = upload_book(client, "original-name.txt", BOOK_ONE_TEXT)

        patch_response = client.patch(
            f"/api/books/{book['id']}",
            json={
                "title": "\u65b0\u7684\u4e66\u540d",
                "description": "\u65b0\u7684\u7b80\u4ecb",
            },
        )
        detail_response = client.get(f"/api/books/{book['id']}")
        bookshelf_response = client.get("/api/books")

    assert patch_response.status_code == 200
    patched_payload = patch_response.json()
    assert patched_payload["title"] == "\u65b0\u7684\u4e66\u540d"
    assert patched_payload["file_name"] == "original-name.txt"
    assert patched_payload["description"] == "\u65b0\u7684\u7b80\u4ecb"

    assert detail_response.status_code == 200
    detail_payload = detail_response.json()
    assert detail_payload["title"] == "\u65b0\u7684\u4e66\u540d"
    assert detail_payload["file_name"] == "original-name.txt"
    assert detail_payload["description"] == "\u65b0\u7684\u7b80\u4ecb"

    assert bookshelf_response.status_code == 200
    assert bookshelf_response.json()[0]["title"] == "\u65b0\u7684\u4e66\u540d"


def test_put_book_updates_metadata_and_detail_returns_recent_read_fields(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        book = upload_book(client, "metadata.txt", BOOK_ONE_TEXT)
        progress_time = datetime(2026, 3, 15, 10, 30, tzinfo=timezone.utc)
        progress_response = client.put(
            f"/api/books/{book['id']}/progress",
            json={
                "chapter_index": 1,
                "char_offset": 12,
                "percent": 56.0,
                "updated_at": progress_time.isoformat(),
            },
        )
        assert progress_response.status_code == 200

        update_response = client.put(
            f"/api/books/{book['id']}",
            json={
                "author": "Liu Cixin",
                "description": "\u7b2c\u4e00\u884c\u7b80\u4ecb\n\u7b2c\u4e8c\u884c\u7b80\u4ecb",
            },
        )
        detail_response = client.get(f"/api/books/{book['id']}")

    assert update_response.status_code == 200
    detail_payload = detail_response.json()
    assert detail_payload["author"] == "Liu Cixin"
    assert detail_payload["description"] == "\u7b2c\u4e00\u884c\u7b80\u4ecb\n\u7b2c\u4e8c\u884c\u7b80\u4ecb"
    assert datetime.fromisoformat(detail_payload["recent_read_at"].replace("Z", "+00:00")) == progress_time
    assert detail_payload["progress_percent"] == 56.0
    assert detail_payload["cover_url"] is None


def test_cover_upload_and_delete_persist_cover_metadata(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        book = upload_book(client, "cover-book.txt", BOOK_ONE_TEXT)
        upload_response = client.post(
            f"/api/books/{book['id']}/cover",
            files={"file": ("cover.png", COVER_PNG_BYTES, "image/png")},
        )
        detail_after_upload = client.get(f"/api/books/{book['id']}")
        bookshelf_after_upload = client.get("/api/books")
        db_book = get_book_or_none(book["id"])
        assert db_book is not None
        assert db_book.cover_path is not None
        cover_path = Path(db_book.cover_path)
        assert cover_path.exists()
        delete_response = client.delete(f"/api/books/{book['id']}/cover")
        detail_after_delete = client.get(f"/api/books/{book['id']}")

    assert upload_response.status_code == 200
    upload_payload = upload_response.json()
    assert upload_payload["cover_url"] is not None

    assert detail_after_upload.status_code == 200
    assert detail_after_upload.json()["cover_url"] == upload_payload["cover_url"]
    assert bookshelf_after_upload.status_code == 200
    assert bookshelf_after_upload.json()[0]["cover_url"] == upload_payload["cover_url"]

    assert delete_response.status_code == 204
    assert not cover_path.exists()
    assert detail_after_delete.status_code == 200
    assert detail_after_delete.json()["cover_url"] is None


def test_cover_upload_rejects_invalid_image_type(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        book = upload_book(client, "invalid-cover.txt", BOOK_ONE_TEXT)
        response = client.post(
            f"/api/books/{book['id']}/cover",
            files={"file": ("cover.gif", b"GIF89a", "image/gif")},
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "Only jpg, jpeg, png, and webp cover images are supported"


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
        upload_cover(client, book["id"])
        db_book = get_book_or_none(book["id"])
        assert db_book is not None
        normalized_path = Path(db_book.file_path)
        cover_path = Path(db_book.cover_path) if db_book.cover_path else None
        raw_files = list((settings.upload_dir / "raw" / str(db_book.user_id)).glob(f"{normalized_path.stem}_*"))

        response = client.delete(f"/api/books/{book['id']}")

    assert response.status_code == 204
    assert get_book_or_none(book["id"]) is None
    assert not normalized_path.exists()
    if cover_path is not None:
        assert not cover_path.exists()
    assert all(not raw_file.exists() for raw_file in raw_files)


def test_get_books_supports_sorting_and_group_filter(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        user_id = get_admin_user_id()
        alpha = upload_book(client, "alpha.txt", BOOK_ONE_TEXT)
        beta = upload_book(client, "beta.txt", BOOK_TWO_TEXT)
        gamma = upload_book(client, "gamma.txt", BOOK_THREE_TEXT)

        group_response = client.post("/api/book-groups", json={"name": "\u79d1\u5e7b"})
        assert group_response.status_code == 201
        default_group = next(group for group in client.get("/api/book-groups").json() if group["name"] == "\u9ed8\u8ba4\u5206\u7ec4")
        sci_fi_group_id = group_response.json()["id"]

        assign_alpha = client.put(
            f"/api/books/{alpha['id']}/groups",
            json={"group_ids": [default_group["id"], sci_fi_group_id]},
        )
        assign_gamma = client.put(
            f"/api/books/{gamma['id']}/groups",
            json={"group_ids": [default_group["id"], sci_fi_group_id]},
        )
        assert assign_alpha.status_code == 200
        assert assign_gamma.status_code == 200

        create_progress(user_id, alpha["id"], 10.0)
        session = database.create_session()
        try:
            alpha_progress = session.query(ReadingProgress).filter(ReadingProgress.book_id == alpha["id"]).one()
            alpha_progress.updated_at = datetime(2026, 3, 15, 8, 0, tzinfo=timezone.utc)
            session.add(
                ReadingProgress(
                    user_id=user_id,
                    book_id=gamma["id"],
                    chapter_index=0,
                    char_offset=4,
                    percent=20.0,
                    updated_at=datetime(2026, 3, 15, 11, 0, tzinfo=timezone.utc),
                )
            )
            session.commit()
        finally:
            session.close()

        created_response = client.get("/api/books", params={"sort": "created_at"})
        recent_response = client.get("/api/books", params={"sort": "recent_read"})
        title_response = client.get("/api/books", params={"sort": "title"})
        group_recent_response = client.get(
            "/api/books",
            params={"group_id": sci_fi_group_id, "sort": "recent_read"},
        )

    assert created_response.status_code == 200
    assert [item["title"] for item in created_response.json()] == ["gamma", "beta", "alpha"]

    assert recent_response.status_code == 200
    assert [item["title"] for item in recent_response.json()] == ["gamma", "alpha", "beta"]

    assert title_response.status_code == 200
    assert [item["title"] for item in title_response.json()] == ["alpha", "beta", "gamma"]

    assert group_recent_response.status_code == 200
    assert [item["title"] for item in group_recent_response.json()] == ["gamma", "alpha"]
