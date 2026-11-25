from fastapi.testclient import TestClient


def test_create_run_and_status(client: TestClient, auth_headers: dict[str, str]) -> None:
    res = client.post("/api/core/runs", json={"reference_date": "2026-11-25"}, headers=auth_headers)
    assert res.status_code == 200
    run = res.json()
    assert run["week_label"] == "2026년 11월 3주차"
    assert run["created_by"] == "test_admin"

    latest = client.get("/api/core/runs/latest", headers=auth_headers).json()
    assert latest["id"] == run["id"]

    status = client.get(f"/api/core/runs/{run['id']}/status", headers=auth_headers).json()
    assert [s["key"] for s in status["stages"]] == [
        "collect",
        "select",
        "match",
        "law",
        "draft",
        "send",
    ]
    assert all(s["status"] == "waiting" for s in status["stages"])


def test_status_not_found(client: TestClient, auth_headers: dict[str, str]) -> None:
    assert client.get("/api/core/runs/999/status", headers=auth_headers).status_code == 404
