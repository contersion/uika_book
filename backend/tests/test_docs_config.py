from fastapi.testclient import TestClient

from app.core import database
from app.core.config import settings
from app.main import create_application


def create_docs_test_client(monkeypatch, tmp_path, *, debug: bool) -> TestClient:
    db_path = tmp_path / "reader.db"
    data_dir = tmp_path / "data"
    upload_dir = tmp_path / "uploads"

    monkeypatch.setattr(settings, "debug", debug)
    monkeypatch.setattr(settings, "data_dir", data_dir)
    monkeypatch.setattr(settings, "upload_dir", upload_dir)
    monkeypatch.setattr(settings, "database_url", f"sqlite:///{db_path.as_posix()}")
    monkeypatch.setattr(database, "engine", database.build_engine(settings.database_url))

    application = create_application()
    return TestClient(application)


def test_docs_are_disabled_when_debug_is_false(monkeypatch, tmp_path):
    with create_docs_test_client(monkeypatch, tmp_path, debug=False) as client:
        docs_response = client.get("/docs")
        redoc_response = client.get("/redoc")
        openapi_response = client.get("/openapi.json")

    assert docs_response.status_code == 404
    assert redoc_response.status_code == 404
    assert openapi_response.status_code == 404


def test_docs_remain_available_when_debug_is_true(monkeypatch, tmp_path):
    with create_docs_test_client(monkeypatch, tmp_path, debug=True) as client:
        docs_response = client.get("/docs")
        openapi_response = client.get("/openapi.json")

    assert docs_response.status_code == 200
    assert openapi_response.status_code == 200
