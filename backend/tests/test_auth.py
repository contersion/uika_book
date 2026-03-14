from fastapi.testclient import TestClient

from app.core import database
from app.core.config import settings
from app.main import create_application
from app.models import User


def create_test_client(monkeypatch, tmp_path) -> TestClient:
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

    application = create_application()
    return TestClient(application)


def test_startup_creates_default_user(monkeypatch, tmp_path):
    with create_test_client(monkeypatch, tmp_path):
        session = database.create_session()
        try:
            user = session.query(User).filter(User.username == "admin").one_or_none()
        finally:
            session.close()

    assert user is not None
    assert user.username == "admin"
    assert user.password_hash != "admin123"


def test_login_returns_access_token(monkeypatch, tmp_path):
    with create_test_client(monkeypatch, tmp_path) as client:
        response = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "admin123"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert payload["access_token"]


def test_login_rejects_invalid_password(monkeypatch, tmp_path):
    with create_test_client(monkeypatch, tmp_path) as client:
        response = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "wrong-password"},
        )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password"


def test_me_requires_authentication(monkeypatch, tmp_path):
    with create_test_client(monkeypatch, tmp_path) as client:
        response = client.get("/api/auth/me")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_me_rejects_invalid_token(monkeypatch, tmp_path):
    with create_test_client(monkeypatch, tmp_path) as client:
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer malformed.token"},
        )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired token"


def test_me_returns_current_user(monkeypatch, tmp_path):
    with create_test_client(monkeypatch, tmp_path) as client:
        login_response = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "admin123"},
        )
        access_token = login_response.json()["access_token"]

        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )

    assert response.status_code == 200
    assert response.json()["username"] == "admin"
    assert "password_hash" not in response.json()
