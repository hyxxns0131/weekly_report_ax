"""공통 테스트 설정 (KHS). 가짜 관리자 계정과 임시 DB를 쓴다. 실제 .env 값은 쓰지 않는다."""

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

TEST_USER = "test_admin"
TEST_PASSWORD = "test-password-123"


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setenv("ADMIN_USERNAME", TEST_USER)
    monkeypatch.setenv("ADMIN_PASSWORD", TEST_PASSWORD)
    monkeypatch.setenv("AUTH_SECRET_KEY", "test-secret-key-for-pytest-only")
    monkeypatch.setenv("LOCAL_DB_PATH", str(tmp_path / "weekly.db"))
    monkeypatch.setenv("LLM_ENABLED", "false")

    from app.core.config import get_settings

    get_settings.cache_clear()
    from app.main import app

    with TestClient(app) as c:
        yield c
    get_settings.cache_clear()


@pytest.fixture
def auth_headers(client: TestClient) -> dict[str, str]:
    res = client.post(
        "/api/core/auth/login", json={"username": TEST_USER, "password": TEST_PASSWORD}
    )
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.json()['token']}"}
