from fastapi.testclient import TestClient

from tests.conftest import TEST_USER


def test_health_is_open(client: TestClient) -> None:
    res = client.get("/api/core/health")
    assert res.status_code == 200
    assert res.json()["login_configured"] is True


def test_login_wrong_password(client: TestClient) -> None:
    res = client.post("/api/core/auth/login", json={"username": TEST_USER, "password": "wrong"})
    assert res.status_code == 401


def test_apis_need_login(client: TestClient) -> None:
    assert client.get("/api/core/auth/me").status_code == 401
    assert client.post("/api/core/runs", json={}).status_code == 401
    assert client.get("/api/b1/runs/1/items").status_code in (401, 404)


def test_me_and_logout(client: TestClient, auth_headers: dict[str, str]) -> None:
    assert client.get("/api/core/auth/me", headers=auth_headers).json() == {"username": TEST_USER}
    assert client.post("/api/core/auth/logout", headers=auth_headers).status_code == 204
    assert client.get("/api/core/auth/me", headers=auth_headers).status_code == 401


def test_bad_token(client: TestClient) -> None:
    res = client.get("/api/core/auth/me", headers={"Authorization": "Bearer abc.def"})
    assert res.status_code == 401
