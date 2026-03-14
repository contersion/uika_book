from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]


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


def test_dockerfile_exists_with_expected_runtime_command():
    dockerfile = BACKEND_DIR / "Dockerfile"
    assert dockerfile.exists(), "Dockerfile should exist for deployment"

    content = dockerfile.read_text(encoding="utf-8")
    assert "WORKDIR /app" in content
    assert "COPY requirements.txt ./" in content
    assert 'CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]' in content


def test_dockerignore_excludes_local_runtime_artifacts():
    dockerignore = BACKEND_DIR / ".dockerignore"
    assert dockerignore.exists(), ".dockerignore should exist for a clean Docker build context"

    content = dockerignore.read_text(encoding="utf-8")
    assert ".venv" in content
    assert "__pycache__" in content
    assert "data" in content
    assert "uploads" in content
