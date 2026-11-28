"""B2-05 Gmail 초안함 저장 → 담당자 승인 → 발송 (가짜 Gmail, 가상 고객사 A사·B사)."""

from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.b2_mail.send import gmail_draft
from tests.b2.send.conftest import FAKE_TO, FakeDrafts, set_env

REAL_GMAIL_SERVICE = gmail_draft.gmail_service  # conftest가 가짜로 바꾸기 전 진짜 함수

H = dict[str, str]


def _gmail(client: TestClient, h: H, draft_id: int) -> Any:
    return client.post(f"/api/b2/drafts/{draft_id}/gmail-draft", headers=h)


def _approve(client: TestClient, h: H, draft_id: int) -> Any:
    return client.post(
        f"/api/b2/drafts/{draft_id}/approve", json={"acknowledge_warnings": True}, headers=h
    )


def _send(client: TestClient, h: H, draft_id: int) -> Any:
    return client.post(f"/api/b2/drafts/{draft_id}/send", headers=h)


# ── Gmail 초안함 저장 ─────────────────────────────────────


def test_no_gmail_permission_stops_safely(
    client: TestClient,
    auth_headers: H,
    drafts: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """토큰에 Gmail 권한이 없으면 503 + 쉬운 안내, 아무것도 저장하지 않는다."""
    from app.core import gmail_client

    def no_scope(scopes: list[str] | None = None) -> Any:
        raise gmail_client.GoogleAuthError("구글 토큰에 필요한 권한이 없습니다(gmail.compose).")

    # conftest의 가짜 Gmail 대신 진짜 연결 함수를 쓰되, 인증 단계에서 권한 없음이 나게 한다
    monkeypatch.setattr(gmail_draft, "gmail_service", REAL_GMAIL_SERVICE)
    monkeypatch.setattr(gmail_client, "get_credentials", no_scope)
    res = _gmail(client, auth_headers, drafts["staff"]["id"])
    assert res.status_code == 503
    assert "Gmail 권한이 없습니다" in res.json()["detail"]
    got = client.get(f"/api/b2/runs/{drafts['_run']['id']}/drafts", headers=auth_headers).json()
    assert all(d["gmail_draft_id"] is None for d in got)


def test_save_creates_then_updates_same_gmail_draft(
    client: TestClient, auth_headers: H, drafts: dict[str, Any], fake_gmail: FakeDrafts
) -> None:
    did = drafts["staff"]["id"]
    first = _gmail(client, auth_headers, did)
    assert first.status_code == 200, first.text
    gid = first.json()["gmail_draft_id"]
    second = _gmail(client, auth_headers, did)
    assert second.json()["gmail_draft_id"] == gid
    assert fake_gmail.calls == [f"create:{gid}", f"update:{gid}"]  # 두 번 눌러도 초안은 1개
    assert fake_gmail.sent == []  # 저장은 발송이 아니다


def test_saved_message_has_subject_to_and_html_table(
    client: TestClient, auth_headers: H, drafts: dict[str, Any], fake_gmail: FakeDrafts
) -> None:
    staff = drafts["staff"]
    gid = _gmail(client, auth_headers, staff["id"]).json()["gmail_draft_id"]
    msg = fake_gmail.message(gid)
    assert msg["Subject"] == staff["subject"]
    assert msg["To"] == FAKE_TO
    assert msg["From"] is None  # GMAIL_SENDER가 비면 로그인한 계정으로 나간다
    parts = {p.get_content_type(): p for p in msg.walk()}
    assert "text/plain" in parts and "text/html" in parts
    html = parts["text/html"].get_payload(decode=True).decode("utf-8")
    assert "<table" in html and "<th" in html


def test_text_format_has_no_html(
    client: TestClient,
    auth_headers: H,
    drafts: dict[str, Any],
    fake_gmail: FakeDrafts,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(gmail_draft, "mail_config", lambda: {"body_format": "text"})
    gid = _gmail(client, auth_headers, drafts["staff"]["id"]).json()["gmail_draft_id"]
    types = {p.get_content_type() for p in fake_gmail.message(gid).walk()}
    assert "text/html" not in types


def test_customer_mail_saved_without_recipient(
    client: TestClient, auth_headers: H, drafts: dict[str, Any], fake_gmail: FakeDrafts
) -> None:
    """고객사 메일 주소는 아직 없다: 받는 사람 없이 초안만 저장 (Gmail에서 직접 채움)."""
    gid = _gmail(client, auth_headers, drafts["C001"]["id"]).json()["gmail_draft_id"]
    assert fake_gmail.message(gid)["To"] is None


def test_deleted_in_gmail_creates_new(
    client: TestClient, auth_headers: H, drafts: dict[str, Any], fake_gmail: FakeDrafts
) -> None:
    did = drafts["staff"]["id"]
    old = _gmail(client, auth_headers, did).json()["gmail_draft_id"]
    fake_gmail.fail_update = 404  # 담당자가 Gmail에서 초안을 지움
    new = _gmail(client, auth_headers, did).json()["gmail_draft_id"]
    assert new != old


def test_gmail_error_is_reported(
    client: TestClient, auth_headers: H, drafts: dict[str, Any], fake_gmail: FakeDrafts
) -> None:
    did = drafts["staff"]["id"]
    _gmail(client, auth_headers, did)
    fake_gmail.fail_update = 500
    res = _gmail(client, auth_headers, did)
    assert res.status_code == 502
    assert "Gmail 요청이 실패" in res.json()["detail"]


# ── 발송 ──────────────────────────────────────────────


def test_send_without_approval_is_409(
    client: TestClient, auth_headers: H, drafts: dict[str, Any], fake_gmail: FakeDrafts
) -> None:
    res = _send(client, auth_headers, drafts["staff"]["id"])
    assert res.status_code == 409
    assert fake_gmail.calls == []


def test_send_switch_off_is_403(
    client: TestClient,
    auth_headers: H,
    drafts: dict[str, Any],
    fake_gmail: FakeDrafts,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    set_env(monkeypatch, "MAIL_SEND_ENABLED", "false")
    did = drafts["staff"]["id"]
    assert _approve(client, auth_headers, did).status_code == 200
    res = _send(client, auth_headers, did)
    assert res.status_code == 403
    assert fake_gmail.sent == []


def test_send_without_recipient_is_409(
    client: TestClient,
    auth_headers: H,
    drafts: dict[str, Any],
    fake_gmail: FakeDrafts,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    set_env(monkeypatch, "GMAIL_STAFF_TO", "")
    did = drafts["staff"]["id"]
    _approve(client, auth_headers, did)
    res = _send(client, auth_headers, did)
    assert res.status_code == 409
    assert "받는 사람" in res.json()["detail"]
    # 고객사 메일도 주소 연결 전이라 막힌다
    cid = drafts["C001"]["id"]
    _approve(client, auth_headers, cid)
    assert _send(client, auth_headers, cid).status_code == 409
    assert fake_gmail.sent == []


def test_send_success_locks_draft(
    client: TestClient, auth_headers: H, drafts: dict[str, Any], fake_gmail: FakeDrafts
) -> None:
    h, did, run_id = auth_headers, drafts["staff"]["id"], drafts["_run"]["id"]
    _approve(client, h, did)
    res = _send(client, h, did)
    assert res.status_code == 200, res.text
    d = res.json()
    assert d["status"] == "sent" and d["sent_at"] and d["gmail_message_id"]
    assert fake_gmail.sent == [d["gmail_draft_id"]]
    # 발송 전에 승인한 본문으로 Gmail 초안을 만들고 그 초안을 보냈다
    assert fake_gmail.calls[-2:] == [f"create:{d['gmail_draft_id']}", f"send:{d['gmail_draft_id']}"]

    # 보낸 뒤에는 다시 보내기·저장·승인·고치기가 모두 막힌다
    assert _send(client, h, did).status_code == 409
    assert _gmail(client, h, did).status_code == 409
    assert _approve(client, h, did).status_code == 409
    patched = client.patch(f"/api/b2/drafts/{did}", json={"final_body": "바꾼 글"}, headers=h)
    assert patched.status_code == 409
    assert len(fake_gmail.sent) == 1

    # 초안을 다시 만들어도 보낸 초안은 그대로
    client.post(f"/api/b2/runs/{run_id}/drafts", headers=h)
    again = next(
        x for x in client.get(f"/api/b2/runs/{run_id}/drafts", headers=h).json() if x["id"] == did
    )
    assert again["status"] == "sent" and again["ai_body"] == d["ai_body"]


def test_send_failure_keeps_approved(
    client: TestClient, auth_headers: H, drafts: dict[str, Any], fake_gmail: FakeDrafts
) -> None:
    did = drafts["staff"]["id"]
    _approve(client, auth_headers, did)
    fake_gmail.fail_send = 500
    res = _send(client, auth_headers, did)
    assert res.status_code == 502
    d = client.get(f"/api/b2/runs/{drafts['_run']['id']}/drafts", headers=auth_headers).json()
    assert next(x for x in d if x["id"] == did)["status"] == "approved"


def test_send_info_hides_addresses(client: TestClient, auth_headers: H) -> None:
    info = client.get("/api/b2/send/info", headers=auth_headers).json()
    assert info == {"mail_send_enabled": True, "staff_to_count": 2, "body_format": "html"}
    assert "example.com" not in str(info)
