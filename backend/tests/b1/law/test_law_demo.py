"""B1-12·13 법령 개정 데모 (저장된 응답). 법령 번호·날짜·내용은 모두 가상이다."""

from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.b1_select.law import law_api, new_in_force
from app.core.schema import LawChange


def _run(client: TestClient, h: dict[str, str]) -> int:
    res = client.post("/api/core/runs", json={"reference_date": "2026-11-25"}, headers=h)
    return int(res.json()["id"])


def test_demo_law_in_force_only(
    client: TestClient, auth_headers: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("LAW_API_OC", "")  # 키 없음 + demo 모드 → 그래도 정상 동작

    def no_network(*_: object, **__: object) -> object:
        raise AssertionError("데모 모드에서는 법제처 API를 부르지 않는다")

    monkeypatch.setattr(law_api, "search_admrul", no_network)
    h = auth_headers
    run_id = _run(client, h)
    res = client.post(f"/api/b1/runs/{run_id}/law", headers=h)
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["errors"] == []
    assert body["found"] == 2 and body["added"] == 1

    laws = client.get(f"/api/b1/runs/{run_id}/law", headers=h).json()
    assert len(laws) == 1
    law = laws[0]
    assert law["law_name"] == "식품의 기준 및 규격"
    assert law["effective_at"] == "2026-11-20"
    assert law["number"] == "제2026-000호(가상)"
    assert law["source_url"] == "https://example.com/demo/law/DEMO0001"
    assert law["ai_summary"].startswith("[가상 데모]")
    assert law["related_food_types"] == ["냉동새우", "과자"]


def test_future_effective_excluded() -> None:
    start, end = date(2026, 11, 16), date(2026, 11, 22)
    now = LawChange(id="law:a", effective_at=date(2026, 11, 20))
    future = LawChange(id="law:b", effective_at=date(2027, 1, 1))
    assert [c.id for c in new_in_force.pick([now, future], start, end, set())] == ["law:a"]
    assert new_in_force.pick([now], start, end, {"law:a"}) == []
