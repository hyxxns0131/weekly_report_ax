"""B2-05 테스트 공통: 진짜 Gmail 대신 가짜 Gmail을 쓴다. 실제 .env의 주소·발송 스위치도 덮어쓴다."""

import base64
import email
from collections.abc import Iterator
from email.message import Message
from email.policy import default
from typing import Any

import pytest
from fastapi.testclient import TestClient

from tests.b1.collect.test_upload_analyze import CSV
from tests.b2.draft.test_draft_revision import b1_inprocess  # noqa: F401 (fixture)

FAKE_TO = "staff-a@example.com, staff-b@example.com"


class FakeHttpError(Exception):
    """googleapiclient HttpError 흉내: resp.status만 쓴다."""

    def __init__(self, status: int) -> None:
        super().__init__(f"HTTP {status}")
        self.resp = type("Resp", (), {"status": status})()


class _Req:
    def __init__(self, fn: Any) -> None:
        self.fn = fn

    def execute(self) -> Any:
        return self.fn()


class FakeDrafts:
    def __init__(self) -> None:
        self.store: dict[str, str] = {}  # Gmail 초안 ID → raw
        self.calls: list[str] = []
        self.sent: list[str] = []
        self.fail_update: int | None = None
        self.fail_send: int | None = None
        self._n = 0

    def create(self, userId: str, body: dict[str, Any]) -> _Req:
        def run() -> dict[str, str]:
            self._n += 1
            gid = f"g{self._n}"
            self.store[gid] = body["message"]["raw"]
            self.calls.append(f"create:{gid}")
            return {"id": gid}

        return _Req(run)

    def update(self, userId: str, id: str, body: dict[str, Any]) -> _Req:
        def run() -> dict[str, str]:
            self.calls.append(f"update:{id}")
            if self.fail_update:
                raise FakeHttpError(self.fail_update)
            self.store[id] = body["message"]["raw"]
            return {"id": id}

        return _Req(run)

    def send(self, userId: str, body: dict[str, Any]) -> _Req:
        def run() -> dict[str, str]:
            self.calls.append(f"send:{body['id']}")
            if self.fail_send:
                raise FakeHttpError(self.fail_send)
            self.sent.append(body["id"])
            return {"id": f"m-{body['id']}"}

        return _Req(run)

    def message(self, gid: str) -> Message:
        return email.message_from_bytes(base64.urlsafe_b64decode(self.store[gid]), policy=default)


class FakeGmail:
    def __init__(self) -> None:
        self.drafts_api = FakeDrafts()

    def users(self) -> "FakeGmail":
        return self

    def drafts(self) -> FakeDrafts:
        return self.drafts_api


@pytest.fixture(autouse=True)
def fake_gmail(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> Iterator[FakeDrafts]:
    """모든 send 테스트에 자동 적용: 진짜 Gmail로 나가는 길을 막는다."""
    from app.b2_mail.send import gmail_draft
    from app.core.config import get_settings

    monkeypatch.setenv("GMAIL_STAFF_TO", FAKE_TO)
    monkeypatch.setenv("GMAIL_SENDER", "")
    monkeypatch.setenv("MAIL_SEND_ENABLED", "true")
    get_settings.cache_clear()
    fake = FakeGmail()
    monkeypatch.setattr(gmail_draft, "gmail_service", lambda: fake)
    yield fake.drafts_api
    get_settings.cache_clear()


def set_env(monkeypatch: pytest.MonkeyPatch, name: str, value: str) -> None:
    from app.core.config import get_settings

    monkeypatch.setenv(name, value)
    get_settings.cache_clear()


@pytest.fixture
def drafts(
    client: TestClient,
    auth_headers: dict[str, str],
    b1_inprocess: None,  # noqa: F811
) -> dict[str, dict[str, Any]]:
    """가상 자료로 초안을 만들고 {"staff": 담당자용, "C001": A사, ...}로 돌려준다."""
    h = auth_headers
    run_id = client.post("/api/core/runs", json={"reference_date": "2026-11-25"}, headers=h).json()[
        "id"
    ]
    client.post(f"/api/b1/runs/{run_id}/upload", json={"kind": "csv", "content": CSV}, headers=h)
    client.post(f"/api/b1/runs/{run_id}/analyze", headers=h)
    made = client.post(f"/api/b2/runs/{run_id}/drafts", headers=h).json()
    out = {(d["customer_id"] or "staff"): d for d in made}
    out["_run"] = {"id": run_id}
    return out
