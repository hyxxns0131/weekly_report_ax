"""B2-04 초안 고치기·이력 규칙 (가상 자료, 가상 고객사 A사·B사)."""

from typing import Any

import pytest
from fastapi.testclient import TestClient

from tests.b1.collect.test_upload_analyze import CSV

AI_CHANGED = "AI 초안 바뀜"
REVOKED = "AI 초안이 바뀌어 승인이 풀렸습니다"


@pytest.fixture
def b1_inprocess(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    from app.b2_mail import input as b2_input

    def fake_get(path: str, token: str | None) -> Any:
        res = client.get(f"/api/b1{path}", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200, res.text
        return res.json()

    monkeypatch.setattr(b2_input, "_get", fake_get)


@pytest.fixture
def draft_a(client: TestClient, auth_headers: dict[str, str], b1_inprocess: None) -> dict[str, Any]:
    """A사(C001) 고객사 메일 초안 하나를 만든다."""
    h = auth_headers
    run_id = client.post("/api/core/runs", json={"reference_date": "2026-11-25"}, headers=h).json()[
        "id"
    ]
    client.post(f"/api/b1/runs/{run_id}/upload", json={"kind": "csv", "content": CSV}, headers=h)
    client.post(f"/api/b1/runs/{run_id}/analyze", headers=h)
    drafts = client.post(f"/api/b2/runs/{run_id}/drafts", headers=h).json()
    a: dict[str, Any] = next(d for d in drafts if d["customer_id"] == "C001")
    return a


def _patch(client: TestClient, h: dict[str, str], draft_id: int, body: str) -> Any:
    res = client.patch(f"/api/b2/drafts/{draft_id}", json={"final_body": body}, headers=h)
    assert res.status_code == 200, res.text
    return res.json()


def _history(client: TestClient, h: dict[str, str], draft_id: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = client.get(f"/api/b2/drafts/{draft_id}/history", headers=h).json()
    return rows


def _approve(client: TestClient, h: dict[str, str], draft_id: int) -> Any:
    return client.post(
        f"/api/b2/drafts/{draft_id}/approve", json={"acknowledge_warnings": True}, headers=h
    ).json()


def test_same_body_save_is_noop(
    client: TestClient, auth_headers: dict[str, str], draft_a: dict[str, Any]
) -> None:
    h, did = auth_headers, draft_a["id"]
    assert _approve(client, h, did)["status"] == "approved"
    # AI 본문 그대로 저장 → 이력도 없고 승인도 그대로
    same = _patch(client, h, did, draft_a["ai_body"])
    assert same["status"] == "approved" and same["final_body"] is None
    assert _history(client, h, did) == []
    # 고친 뒤 같은 글로 또 저장 → 이력 1건 그대로
    _patch(client, h, did, "수정본")
    _patch(client, h, did, "수정본")
    assert len(_history(client, h, did)) == 1


def test_edited_body_is_checked(
    client: TestClient, auth_headers: dict[str, str], draft_a: dict[str, Any]
) -> None:
    h, did = auth_headers, draft_a["id"]
    got = _patch(client, h, did, "B사에도 안내드린 9999건 관련입니다.")
    assert "다른 고객사명 포함: B사" in got["warnings"]
    assert any(w.startswith("원문에 없는 숫자") and "9999" in w for w in got["warnings"])
    # 문제를 지우고 다시 저장하면 경고도 사라진다
    clean = _patch(client, h, did, "안녕하세요. 안내드립니다.")
    assert not any(w.startswith(("다른 고객사명", "원문에 없는 숫자")) for w in clean["warnings"])


def test_check_failure_still_saves(
    client: TestClient,
    auth_headers: dict[str, str],
    draft_a: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.b2_mail import input as b2_input

    def down(path: str, token: str | None) -> Any:
        raise b2_input.B1Unavailable("b1 꺼짐")

    monkeypatch.setattr(b2_input, "_get", down)
    got = _patch(client, auth_headers, draft_a["id"], "고친 본문")
    assert got["final_body"] == "고친 본문"
    assert any(w.startswith("고친 본문을 검사하지 못했습니다") for w in got["warnings"])


def test_ai_changed_mark_after_edit(
    client: TestClient,
    auth_headers: dict[str, str],
    draft_a: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.b2_mail.draft import customer

    h, did, run_id = auth_headers, draft_a["id"], draft_a["run_id"]
    _patch(client, h, did, "담당자 수정본")
    monkeypatch.setattr(customer, "body", lambda *a, **k: "새 AI 본문")
    again = client.post(f"/api/b2/runs/{run_id}/drafts", headers=h).json()
    a = next(d for d in again if d["id"] == did)
    assert a["final_body"] == "담당자 수정본" and a["ai_body"] == "새 AI 본문"
    assert any(w.startswith(AI_CHANGED) for w in a["warnings"])
    # 한 번 더 만들어도(AI 본문 그대로) 담당자가 확인 전이면 표시가 남는다
    again2 = client.post(f"/api/b2/runs/{run_id}/drafts", headers=h).json()
    a2 = next(d for d in again2 if d["id"] == did)
    assert any(w.startswith(AI_CHANGED) for w in a2["warnings"])
    # 담당자가 고쳐 저장하면 표시가 사라진다
    saved = _patch(client, h, did, "담당자 수정본 2")
    assert not any(w.startswith(AI_CHANGED) for w in saved["warnings"])


def test_approved_ai_body_change_revokes(
    client: TestClient,
    auth_headers: dict[str, str],
    draft_a: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.b2_mail.draft import customer

    h, did, run_id = auth_headers, draft_a["id"], draft_a["run_id"]
    assert _approve(client, h, did)["status"] == "approved"
    # AI 본문이 그대로면 승인 유지
    same = client.post(f"/api/b2/runs/{run_id}/drafts", headers=h).json()
    assert next(d for d in same if d["id"] == did)["status"] == "approved"
    # 승인한 AI 본문이 바뀌면 승인이 풀린다
    monkeypatch.setattr(customer, "body", lambda *a, **k: "새 AI 본문")
    again = client.post(f"/api/b2/runs/{run_id}/drafts", headers=h).json()
    a = next(d for d in again if d["id"] == did)
    assert a["status"] == "draft"
    assert any(w.startswith(REVOKED) for w in a["warnings"])


def test_history_newest_first_with_body(
    client: TestClient, auth_headers: dict[str, str], draft_a: dict[str, Any]
) -> None:
    h, did = auth_headers, draft_a["id"]
    _patch(client, h, did, "첫 수정")
    _patch(client, h, did, "둘째 수정")
    rows = _history(client, h, did)
    assert [r["body"] for r in rows] == ["둘째 수정", "첫 수정"]
    assert all(r["edited_by"] == "test_admin" for r in rows)
    # 예전 글로 되돌리기 = 그 글로 다시 저장 → 이력이 하나 더 쌓인다
    back = _patch(client, h, did, rows[1]["body"])
    assert back["final_body"] == "첫 수정"
    assert len(_history(client, h, did)) == 3


def test_sent_or_missing_draft(client: TestClient, auth_headers: dict[str, str]) -> None:
    res = client.patch("/api/b2/drafts/99999", json={"final_body": "x"}, headers=auth_headers)
    assert res.status_code == 404


def test_regenerate_keeps_sent_draft(
    client: TestClient, auth_headers: dict[str, str], draft_a: dict[str, Any]
) -> None:
    """발송한 초안은 다시 만들기를 눌러도 본문·경고·상태가 그대로다 (보낸 기록)."""
    from app.core.storage import repo

    did = draft_a["id"]
    repo.update_draft(did, status="sent", ai_body="보낸 그대로의 본문", warnings=["보낸 때 경고"])
    client.post(f"/api/b2/runs/{draft_a['run_id']}/drafts", headers=auth_headers)
    got = repo.get_draft(did)
    assert got is not None
    assert got.status == "sent"
    assert got.ai_body == "보낸 그대로의 본문"
    assert got.warnings == ["보낸 때 경고"]
