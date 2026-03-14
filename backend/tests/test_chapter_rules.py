from contextlib import contextmanager

from fastapi.testclient import TestClient

from app.core import database
from app.core.config import settings
from app.main import create_application
from app.models import ChapterRule


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


def test_startup_seeds_builtin_chapter_rules(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path):
        session = database.create_session()
        try:
            builtin_rules = session.query(ChapterRule).filter(ChapterRule.is_builtin.is_(True)).all()
        finally:
            session.close()

    assert len(builtin_rules) >= 4
    assert any(rule.rule_name == "中文章节规则" for rule in builtin_rules)
    assert any(rule.rule_name == "英文章节规则" for rule in builtin_rules)
    assert any(rule.rule_name == "卷章混合规则" for rule in builtin_rules)
    assert any(rule.rule_name == "单章节全文模式" for rule in builtin_rules)


def test_get_chapter_rules_returns_builtin_and_user_rules(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        create_response = client.post(
            "/api/chapter-rules",
            json={
                "rule_name": "自定义规则",
                "regex_pattern": r"^Scene\\s+\\d+",
                "flags": "MULTILINE",
                "description": "custom",
                "is_default": False,
            },
        )
        assert create_response.status_code == 201

        response = client.get("/api/chapter-rules")

    assert response.status_code == 200
    rule_names = {item["rule_name"] for item in response.json()}
    assert "中文章节规则" in rule_names
    assert "自定义规则" in rule_names


def test_create_custom_rule_can_replace_default(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        response = client.post(
            "/api/chapter-rules",
            json={
                "rule_name": "我的默认规则",
                "regex_pattern": r"^Part\\s+\\d+",
                "flags": "MULTILINE",
                "description": "mine",
                "is_default": True,
            },
        )
        list_response = client.get("/api/chapter-rules")

    assert response.status_code == 201
    assert response.json()["is_builtin"] is False
    default_rules = [item for item in list_response.json() if item["is_default"]]
    assert len(default_rules) == 1
    assert default_rules[0]["rule_name"] == "我的默认规则"


def test_put_custom_rule_updates_fields(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        create_response = client.post(
            "/api/chapter-rules",
            json={
                "rule_name": "旧规则",
                "regex_pattern": r"^Old",
                "flags": "",
                "description": "before",
                "is_default": False,
            },
        )
        rule_id = create_response.json()["id"]

        response = client.put(
            f"/api/chapter-rules/{rule_id}",
            json={
                "rule_name": "新规则",
                "regex_pattern": r"^New",
                "flags": "IGNORECASE",
                "description": "after",
                "is_default": True,
            },
        )

    assert response.status_code == 200
    assert response.json()["rule_name"] == "新规则"
    assert response.json()["is_default"] is True


def test_put_builtin_rule_rejects_core_field_changes(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        rules_response = client.get("/api/chapter-rules")
        builtin_rule_id = next(item["id"] for item in rules_response.json() if item["is_builtin"])

        response = client.put(
            f"/api/chapter-rules/{builtin_rule_id}",
            json={"rule_name": "不能改"},
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "Built-in rules only allow updating the default status"


def test_delete_builtin_rule_is_forbidden(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        rules_response = client.get("/api/chapter-rules")
        builtin_rule_id = next(item["id"] for item in rules_response.json() if item["is_builtin"])

        response = client.delete(f"/api/chapter-rules/{builtin_rule_id}")

    assert response.status_code == 400
    assert response.json()["detail"] == "Built-in rules cannot be deleted"


def test_delete_custom_rule_removes_it(monkeypatch, tmp_path):
    with authenticated_client(monkeypatch, tmp_path) as client:
        create_response = client.post(
            "/api/chapter-rules",
            json={
                "rule_name": "待删除规则",
                "regex_pattern": r"^Delete",
                "flags": "",
                "description": None,
                "is_default": False,
            },
        )
        rule_id = create_response.json()["id"]

        delete_response = client.delete(f"/api/chapter-rules/{rule_id}")
        list_response = client.get("/api/chapter-rules")

    assert delete_response.status_code == 204
    rule_ids = {item["id"] for item in list_response.json()}
    assert rule_id not in rule_ids
