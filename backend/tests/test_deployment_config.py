from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = BACKEND_DIR.parent


def _parse_env_file(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", maxsplit=1)
        result[key] = value
    return result


def test_env_example_uses_runtime_relative_storage_paths():
    env_values = _parse_env_file(BACKEND_DIR / ".env.example")

    assert env_values["DATA_DIR"] == "data"
    assert env_values["UPLOAD_DIR"] == "uploads"


def test_root_env_example_uses_custom_host_ports():
    env_values = _parse_env_file(ROOT_DIR / ".env.example")

    assert env_values["BACKEND_PORT"] == "7000"
    assert env_values["FRONTEND_PORT"] == "21412"
    assert env_values["CORS_ORIGINS"] == '["http://localhost:21412","http://127.0.0.1:21412"]'


def test_dockerfile_exists_with_expected_runtime_command():
    dockerfile = BACKEND_DIR / "Dockerfile"
    assert dockerfile.exists(), "Dockerfile should exist for deployment"

    content = dockerfile.read_text(encoding="utf-8")
    assert "WORKDIR /app" in content
    assert "COPY requirements.txt ./" in content
    assert 'CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]' in content


def test_root_docker_compose_matches_runtime_and_host_ports():
    compose_file = ROOT_DIR / "docker-compose.yml"
    assert compose_file.exists(), "docker-compose.yml should exist at the repository root"

    content = compose_file.read_text(encoding="utf-8")
    assert "PORT: 8000" in content
    assert '${CORS_ORIGINS:-["http://localhost:21412","http://127.0.0.1:21412"]}' in content
    assert '${BACKEND_PORT:-7000}:8000' in content
    assert '${FRONTEND_PORT:-21412}:80' in content


def test_dockerignore_excludes_local_runtime_artifacts():
    dockerignore = BACKEND_DIR / ".dockerignore"
    assert dockerignore.exists(), ".dockerignore should exist for a clean Docker build context"

    content = dockerignore.read_text(encoding="utf-8")
    assert ".venv" in content
    assert "__pycache__" in content
    assert "data" in content
    assert "uploads" in content
