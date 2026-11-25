from fastapi.testclient import TestClient

from app.core.storage import local_db


def test_create_run_and_status(client: TestClient, auth_headers: dict[str, str]) -> None:
    res = client.post("/api/core/runs", json={"reference_date": "2026-11-25"}, headers=auth_headers)
    assert res.status_code == 200
    run = res.json()
    assert run["week_label"] == "2026년 11월 3주차"
    assert run["created_by"] == "test_admin"

    latest = client.get("/api/core/runs/latest", headers=auth_headers).json()
    assert latest["id"] == run["id"]

    status = client.get(f"/api/core/runs/{run['id']}/status", headers=auth_headers).json()
    assert [s["key"] for s in status["steps"]] == [
        "collect",
        "select",
        "extract",
        "match",
        "law",
        "report",
        "draft",
        "send",
        "evaluate",
    ]
    assert status["current"] == {"b1": "collect", "b2": "report"}
    assert status["materials_ready"] is False
    assert status["todos"] == []
    assert not any(s["done"] for s in status["steps"])


def test_status_not_found(client: TestClient, auth_headers: dict[str, str]) -> None:
    assert client.get("/api/core/runs/999/status", headers=auth_headers).status_code == 404


def _seed(run_id: int) -> None:
    """가상 데이터: 검토 필요 검사지시 1건, 무관 1건, 법령 개정 1건 (A사·B사 같은 가명만)."""
    with local_db.connect() as conn:
        for item_id, cat, label in (
            ("manual:1", "inspection_order", "review_needed"),
            ("manual:2", "other", "irrelevant"),
        ):
            conn.execute(
                "INSERT INTO raw_item (id, run_id, source, title, body, collected_at)"
                " VALUES (?, ?, 'manual', '가상 항목', '본문', '2026-11-25T09:00:00+09:00')",
                (item_id, run_id),
            )
            conn.execute(
                "INSERT INTO selection (item_id, ai_label, ai_category) VALUES (?, ?, ?)",
                (item_id, label, cat),
            )
        conn.execute(
            "INSERT INTO extracted_info (item_id, origin_country, food_type_std, violation)"
            " VALUES ('manual:1', '가상국', '가상식품', '가상 검사 항목')"
        )
        conn.execute(
            "INSERT INTO customer_match"
            " (item_id, customer_id, ai_matched, rule, confidence, reason)"
            " VALUES ('manual:1', 'C001', 1, 'origin_food_type', 'high', '가상 근거')"
        )
        conn.execute(
            "INSERT INTO law_change_work (id, run_id, law_name, change_type, ai_summary,"
            " crosscheck) VALUES ('law:1', ?, '가상 고시', '일부개정', 'AI 요지', 'match')",
            (run_id,),
        )


def test_status_counts_and_todos(client: TestClient, auth_headers: dict[str, str]) -> None:
    run = client.post("/api/core/runs", json={}, headers=auth_headers).json()
    _seed(run["id"])
    status = client.get(f"/api/core/runs/{run['id']}/status", headers=auth_headers).json()
    steps = {s["key"]: s for s in status["steps"]}
    assert steps["collect"]["done"] is True
    assert steps["select"]["state"] == "current"
    assert steps["select"]["note"] == "검토 필요 1건"
    assert status["current"]["b1"] == "select"
    keys = [t["key"] for t in status["todos"]]
    assert "review_needed" in keys
    todo = next(t for t in status["todos"] if t["key"] == "review_needed")
    assert todo["href"] == "/collect/?step=select&label=review_needed"


def test_notices_read_and_dismiss(client: TestClient, auth_headers: dict[str, str]) -> None:
    run = client.post("/api/core/runs", json={}, headers=auth_headers).json()
    url = f"/api/core/runs/{run['id']}/notices"
    empty = client.get(url, headers=auth_headers).json()
    assert empty == {"items": [], "unread": 0, "total": 0}

    _seed(run["id"])
    data = client.get(url, headers=auth_headers).json()
    ids = [n["id"] for n in data["items"]]
    assert ids == ["law:1", "inspection:manual:1"]  # 무관 항목은 빠진다
    assert data["unread"] == 2
    law = data["items"][0]
    assert law["summary"] == "AI 요지" and law["summary_is_ai"] is True
    assert law["crosscheck"] == "match"
    insp = data["items"][1]
    assert insp["customers"] == ["C001"]
    assert insp["title"] == "가상국 · 가상식품"

    res = client.patch(
        "/api/core/notices/law:1",
        json={"action": "read", "run_id": run["id"]},
        headers=auth_headers,
    )
    assert res.status_code == 200
    assert res.json()["read_by"] == "test_admin"
    data = client.get(url, headers=auth_headers).json()
    assert data["unread"] == 1 and len(data["items"]) == 2  # 읽어도 지우지 않는다

    client.patch(
        "/api/core/notices/inspection:manual:1",
        json={"action": "dismiss", "run_id": run["id"]},
        headers=auth_headers,
    )
    data = client.get(url, headers=auth_headers).json()
    assert [n["id"] for n in data["items"]] == ["law:1"]
    assert data["unread"] == 0 and data["total"] == 2


def test_notices_need_login(client: TestClient) -> None:
    assert client.get("/api/core/runs/1/notices").status_code == 401
    assert client.patch("/api/core/notices/law:1", json={"action": "read"}).status_code == 401
