"""AI 연결 상태·연결 검사·모델 선택 (C-02). 실제 AI 서버는 부르지 않는다(가짜 응답)."""

import httpx
import pytest
from fastapi.testclient import TestClient

from app.core import llm
from app.core.config import get_settings


@pytest.fixture
def ai_on(monkeypatch: pytest.MonkeyPatch, client: TestClient) -> None:
    monkeypatch.setenv("LLM_ENABLED", "true")
    monkeypatch.setenv("AI_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-not-real")
    get_settings.cache_clear()


def test_status_off_by_default(client: TestClient, auth_headers: dict[str, str]) -> None:
    r = client.get("/api/core/ai/status", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["state"] == "off"


def test_status_needs_login(client: TestClient) -> None:
    assert client.get("/api/core/ai/status").status_code == 401


def test_key_never_returned(ai_on: None, client: TestClient, auth_headers: dict[str, str]) -> None:
    r = client.get("/api/core/ai/status", headers=auth_headers)
    body = r.json()
    assert body["key_set"] is True and body["state"] == "ready"
    assert "sk-test-not-real" not in r.text


def test_choose_model_and_test(
    ai_on: None, client: TestClient, auth_headers: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    r = client.put(
        "/api/core/ai/settings",
        headers=auth_headers,
        json={"provider": "openai", "model": "gpt-test-1"},
    )
    assert r.json()["model"] == "gpt-test-1"

    def fake_get(url: str, **_: object) -> httpx.Response:
        data = {"data": [{"id": "gpt-test-1"}, {"id": "text-embedding-x"}]}
        return httpx.Response(200, json=data, request=httpx.Request("GET", url))

    monkeypatch.setattr(llm.httpx, "get", fake_get)
    t = client.post("/api/core/ai/test", headers=auth_headers).json()
    assert t["ok"] is True and t["available_models"] == ["gpt-test-1"]
    s = client.get("/api/core/ai/status", headers=auth_headers).json()
    assert s["state"] == "ok" and "gpt-test-1" in s["models"]


def test_bad_key(
    ai_on: None, client: TestClient, auth_headers: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    def fake_get(url: str, **_: object) -> httpx.Response:
        return httpx.Response(401, json={}, request=httpx.Request("GET", url))

    monkeypatch.setattr(llm.httpx, "get", fake_get)
    t = client.post("/api/core/ai/test", headers=auth_headers).json()
    assert t["ok"] is False and "401" in t["message"]
    s = client.get("/api/core/ai/status", headers=auth_headers).json()
    assert s["state"] == "error"
