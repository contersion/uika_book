from fastapi.testclient import TestClient

from app.core import database
from app.core.config import settings
from app.main import create_application


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

    return TestClient(create_application())


def test_http_errors_use_unified_error_response(monkeypatch, tmp_path):
    with create_test_client(monkeypatch, tmp_path) as client:
        response = client.get("/api/auth/me")

    assert response.status_code == 401
    payload = response.json()
    assert payload["success"] is False
    assert payload["detail"] == "Not authenticated"
    assert payload["error"]["code"] == "http_401"
    assert payload["error"]["message"] == "Not authenticated"
    assert payload["error"]["details"] is None


def test_validation_errors_use_unified_error_response(monkeypatch, tmp_path):
    with create_test_client(monkeypatch, tmp_path) as client:
        response = client.post("/api/auth/login", json={"username": "admin"})

    assert response.status_code == 422
    payload = response.json()
    assert payload["success"] is False
    assert payload["detail"] == "Request validation failed"
    assert payload["error"]["code"] == "validation_error"
    assert payload["error"]["message"] == "Request validation failed"
    assert isinstance(payload["error"]["details"], list)
    assert payload["error"]["details"]
