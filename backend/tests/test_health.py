from fastapi.testclient import TestClient

from app.core import database
from app.core.config import settings
from app.init_data import init_db
from app.main import create_application


def test_health_endpoint_returns_expected_payload(monkeypatch, tmp_path):
    db_path = tmp_path / "reader.db"
    monkeypatch.setattr(settings, "data_dir", tmp_path / "data")
    monkeypatch.setattr(settings, "upload_dir", tmp_path / "uploads")
    monkeypatch.setattr(settings, "database_url", f"sqlite:///{db_path.as_posix()}")
    monkeypatch.setattr(database, "engine", database.build_engine(settings.database_url))

    application = create_application()

    with TestClient(application) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "app_name": settings.app_name,
        "version": settings.app_version,
    }


def test_init_db_creates_required_runtime_directories(monkeypatch, tmp_path):
    db_path = tmp_path / "reader.db"
    data_dir = tmp_path / "data"
    upload_dir = tmp_path / "uploads"

    monkeypatch.setattr(settings, "data_dir", data_dir)
    monkeypatch.setattr(settings, "upload_dir", upload_dir)
    monkeypatch.setattr(settings, "database_url", f"sqlite:///{db_path.as_posix()}")
    monkeypatch.setattr(database, "engine", database.build_engine(settings.database_url))

    init_db()

    assert data_dir.exists()
    assert upload_dir.exists()
    assert db_path.exists()
