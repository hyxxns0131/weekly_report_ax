"""연결 설정 (C-01). 실제 외부 서버는 부르지 않는다(가짜 응답)."""

import httpx
import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.connections import service

FAKE_KEY = "sb_publishable_test_not_real"


def test_list_needs_login(client: TestClient) -> None:
    assert client.get("/api/core/connections").status_code == 401


def test_list_all(client: TestClient, auth_headers: dict[str, str]) -> None:
    r = client.get("/api/core/connections", headers=auth_headers)
    assert r.status_code == 200
    ids = [c["id"] for c in r.json()]
    assert ids == ["ai", "supabase_read", "supabase_write", "google_drive", "gmail", "law_api"]


def test_missing_setting_test_says_why(client: TestClient, auth_headers: dict[str, str]) -> None:
    r = client.post("/api/core/connections/law_api/test", headers=auth_headers).json()
    assert r["state"] == "no_key"
    assert r["last_test"]["ok"] is False and "LAW_API_OC" in r["last_test"]["message"]


def test_supabase_read_ok_and_key_hidden(
    client: TestClient, auth_headers: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", FAKE_KEY)
    get_settings.cache_clear()

    def fake_get(url: str, **_: object) -> httpx.Response:
        return httpx.Response(200, json=[], request=httpx.Request("GET", url))

    monkeypatch.setattr(service.httpx, "get", fake_get)
    r = client.post("/api/core/connections/supabase_read/test", headers=auth_headers)
    body = r.json()
    assert body["state"] == "ok" and body["state_label"] == "연결됨"
    assert FAKE_KEY not in r.text
    listed = client.get("/api/core/connections", headers=auth_headers)
    assert FAKE_KEY not in listed.text


def test_supabase_bad_key(
    client: TestClient, auth_headers: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", FAKE_KEY)
    get_settings.cache_clear()

    def fake_get(url: str, **_: object) -> httpx.Response:
        return httpx.Response(401, json={}, request=httpx.Request("GET", url))

    monkeypatch.setattr(service.httpx, "get", fake_get)
    body = client.post("/api/core/connections/supabase_read/test", headers=auth_headers).json()
    assert body["state"] == "error" and "키가 맞지 않습니다" in body["last_test"]["message"]


def test_unknown_id(client: TestClient, auth_headers: dict[str, str]) -> None:
    assert client.post("/api/core/connections/nope/test", headers=auth_headers).status_code == 422
