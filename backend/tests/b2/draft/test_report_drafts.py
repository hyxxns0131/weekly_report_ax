"""B2-01~05: 보고서 조립 → 초안 → 수정 → 승인 → 발송 거부 (가상 자료)."""

from typing import Any

import pytest
from fastapi.testclient import TestClient

from tests.b1.collect.test_upload_analyze import CSV


@pytest.fixture
def b1_inprocess(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """b2 input.py가 같은 서버의 b1 API를 HTTP로 부르는 부분을 테스트 클라이언트로 바꾼다."""
    from app.b2_mail import input as b2_input

    def fake_get(path: str, token: str | None) -> Any:
        res = client.get(f"/api/b1{path}", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200, res.text
        return res.json()

    monkeypatch.setattr(b2_input, "_get", fake_get)


def test_report_and_drafts(
    client: TestClient, auth_headers: dict[str, str], b1_inprocess: None
) -> None:
    h = auth_headers
    run_id = client.post("/api/core/runs", json={"reference_date": "2026-11-25"}, headers=h).json()[
        "id"
    ]
    client.post(f"/api/b1/runs/{run_id}/upload", json={"kind": "csv", "content": CSV}, headers=h)
    client.post(f"/api/b1/runs/{run_id}/analyze", headers=h)

    rep = client.post(f"/api/b2/runs/{run_id}/report", headers=h)
    assert rep.status_code == 200, rep.text
    text = rep.json()["text"]
    assert "테스트 위스키" in text
    assert "해당 없습니다" in text  # 섹션 2 법령 없음 → 해당 없음

    drafts = client.post(f"/api/b2/runs/{run_id}/drafts", headers=h).json()
    kinds = sorted((d["kind"], d["customer_id"] or "") for d in drafts)
    assert kinds == [("customer", "C001"), ("customer", "C002"), ("staff_summary", "")]
    a = next(d for d in drafts if d["customer_id"] == "C001")
    assert "테스트 쌀과자" not in a["ai_body"]  # A사 메일에는 A사 관련 항목만
    assert "B사" not in a["ai_body"]

    # 승인 전 발송 → 409
    assert client.post(f"/api/b2/drafts/{a['id']}/send", headers=h).status_code == 409
    ok = client.post(
        f"/api/b2/drafts/{a['id']}/approve", json={"acknowledge_warnings": True}, headers=h
    ).json()
    assert ok["status"] == "approved" and ok["approved_by"] == "test_admin"
    # 발송 꺼짐(MAIL_SEND_ENABLED 기본 false) → 403
    assert client.post(f"/api/b2/drafts/{a['id']}/send", headers=h).status_code == 403
    # 승인 뒤 본문을 고치면 승인이 풀린다
    edited = client.patch(
        f"/api/b2/drafts/{a['id']}", json={"final_body": "수정본"}, headers=h
    ).json()
    assert edited["status"] == "draft" and edited["final_body"] == "수정본"
    assert len(client.get(f"/api/b2/drafts/{a['id']}/history", headers=h).json()) == 1

    # 다시 만들어도 final_body는 그대로
    again = client.post(f"/api/b2/runs/{run_id}/drafts", headers=h).json()
    assert next(d for d in again if d["id"] == a["id"])["final_body"] == "수정본"
