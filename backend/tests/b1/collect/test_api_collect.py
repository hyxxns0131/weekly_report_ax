"""B1-02~06 공식 Open API 수집: .env 설정이 있으면 API, 없으면 수동 업로드(더미 안 씀).

실제 API는 부르지 않는다 (web.get을 가짜 응답으로 바꾼다). 서비스 ID·칸 이름·자료는 모두 가상이다.
"""

import json
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.b1_select.collect import api_client, server_db, service, web
from app.core.storage import public_db

API_SOURCES = [
    "impfood_unfit",
    "impfood_inspection",
    "impfood_law_policy",
    "mfds_notice",
    "gyeongin_newsletter",
]

# 가상 식품안전나라 API 칸 이름 → 우리 칸 이름
# (실제 칸 이름은 API 명세 확인 후 sources.json에 적는다)
UNFIT_MAP = {
    "key": "SEQ",
    "title": "PRDT_NM",
    "date": "DSPS_DT",
    "fields": {
        "제품명": "PRDT_NM",
        "식품유형/품목명": "ITEM_NM",
        "제조국가": "MNF_NTN",
        "제조/수출회사": "MNF_ENTP",
        "위반내역": "VIOL",
    },
}

FOODSAFETY_OK = {
    "I9999": {
        "total_count": "2",
        "RESULT": {"CODE": "INFO-000", "MSG": "정상처리되었습니다."},
        "row": [
            {
                "SEQ": "1",
                "PRDT_NM": "가상 냉동새우",
                "DSPS_DT": "20261118",
                "ITEM_NM": "[수산물] 냉동새우",
                "MNF_NTN": "중국",
                "MNF_ENTP": "GASANG SEAFOOD",
                "VIOL": "이산화황 검출[기준: 불검출]",
            },
            {
                "SEQ": "0",
                "PRDT_NM": "가상 오래된 과자",
                "DSPS_DT": "20261101",
                "ITEM_NM": "과자",
                "MNF_NTN": "베트남",
            },
        ],
    }
}

DATAGO_OK = {
    "response": {
        "header": {"resultCode": "00", "resultMsg": "NORMAL SERVICE."},
        "body": {
            "items": {
                "item": [{"NTC_SJ": "가상 고시 일부개정", "REG_DT": "2026-11-19", "NO": "7"}]
            },
            "totalCount": 1,
        },
    }
}


def _run(client: TestClient, h: dict[str, str]) -> int:
    res = client.post("/api/core/runs", json={"reference_date": "2026-11-25"}, headers=h)
    return int(res.json()["id"])


def _api_mode(
    monkeypatch: pytest.MonkeyPatch, maps: dict[str, dict[str, Any]] | None = None
) -> None:
    original = service.source_config()
    maps = maps or {}

    def cfg() -> list[dict[str, Any]]:
        out = []
        for s in original:
            if s["id"] in API_SOURCES:
                s = {**s, "mode": "api", "api": {"map": maps.get(s["id"], {})}}
            out.append(s)
        return out

    monkeypatch.setattr(service, "source_config", cfg)


def _fake(
    monkeypatch: pytest.MonkeyPatch, answers: dict[str, Any]
) -> list[tuple[str, dict[str, str]]]:
    calls: list[tuple[str, dict[str, str]]] = []

    def fake_get(url: str, params: dict[str, str] | None = None) -> Any:
        calls.append((url, dict(params or {})))
        for key, body in answers.items():
            if key in url:
                text = body if isinstance(body, str) else json.dumps(body, ensure_ascii=False)
                return SimpleNamespace(text=text)
        raise AssertionError(f"모르는 주소: {url}")

    monkeypatch.setattr(web, "get", fake_get)
    return calls


def _collect(client: TestClient, h: dict[str, str], run_id: int) -> dict[str, Any]:
    res = client.post(f"/api/b1/runs/{run_id}/collect", json={"sources": API_SOURCES}, headers=h)
    assert res.status_code == 200, res.text
    return {r["source"]: r for r in res.json()}


def test_no_api_settings_is_manual(
    client: TestClient, auth_headers: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    _api_mode(monkeypatch)
    h = auth_headers
    by = _collect(client, h, _run(client, h))
    for sid in API_SOURCES:
        assert by[sid]["status"] == "manual", by[sid]
        assert by[sid]["message"] == api_client.NO_API_NOTE, by[sid]
        assert not by[sid]["items"]


def test_foodsafety_api_flows_to_customer_match(
    client: TestClient, auth_headers: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    _api_mode(monkeypatch, {"impfood_unfit": UNFIT_MAP})
    monkeypatch.setenv("IMPFOOD_UNFIT_API", "I9999")
    monkeypatch.setenv("FOODSAFETY_API_KEY", "virtual-key")
    calls = _fake(monkeypatch, {"openapi.foodsafetykorea.go.kr": FOODSAFETY_OK})
    h = auth_headers
    run_id = _run(client, h)

    by = _collect(client, h, run_id)
    r = by["impfood_unfit"]
    assert r["status"] == "ok"
    assert "API 1건" in r["message"] and "기간 밖 1건" in r["message"]
    assert server_db.NO_KEY in r["message"]
    assert calls[0][0] == "http://openapi.foodsafetykorea.go.kr/api/virtual-key/I9999/json/1/1000"
    assert by["mfds_notice"]["status"] == "manual"  # 설정 안 한 출처는 수동 업로드

    client.post(f"/api/b1/runs/{run_id}/analyze", headers=h)
    items = {
        i["raw"]["id"]: i for i in client.get(f"/api/b1/runs/{run_id}/items", headers=h).json()
    }
    got = items["impfood_unfit:1"]
    assert got["raw"]["posted_at"] == "2026-11-18"
    assert got["extracted"]["origin_country"] == "중국"
    matches = client.get(f"/api/b1/runs/{run_id}/matches", headers=h).json()
    # 가상 고객사 A사(C001) 키워드: 중국-냉동새우
    assert ("impfood_unfit:1", "C001", "origin_food_type") in {
        (m["item_id"], m["customer_id"], m["rule"]) for m in matches
    }

    status = {
        s["source"]: s for s in client.get(f"/api/b1/runs/{run_id}/sources", headers=h).json()
    }
    assert status["impfood_unfit"]["at"]


def test_datagokr_api_with_guessed_columns(
    client: TestClient, auth_headers: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    _api_mode(monkeypatch)
    monkeypatch.setenv("MFDS_NOTICE_API", "https://apis.data.go.kr/0000000/virtual/getList")
    monkeypatch.setenv("DATA_GO_KR_SERVICE_KEY", "virtual-key")
    calls = _fake(monkeypatch, {"apis.data.go.kr": DATAGO_OK})
    h = auth_headers

    r = _collect(client, h, _run(client, h))["mfds_notice"]
    assert r["status"] == "ok", r
    assert [i["title"] for i in r["items"]] == ["가상 고시 일부개정"]  # 제목 칸(…SJ)을 짐작
    assert r["items"][0]["posted_at"] == "2026-11-19"  # 날짜 칸(…DT)을 짐작
    url, params = calls[0]
    assert url.endswith("/virtual/getList")
    assert params["serviceKey"] == "virtual-key" and params["type"] == "json"


def test_api_error_fails_only_that_source(
    client: TestClient, auth_headers: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    _api_mode(monkeypatch)
    monkeypatch.setenv("IMPFOOD_UNFIT_API", "I9999")
    monkeypatch.setenv("FOODSAFETY_API_KEY", "wrong-key")
    monkeypatch.setenv("MFDS_NOTICE_API", "https://apis.data.go.kr/0000000/virtual/getList")
    monkeypatch.setenv("DATA_GO_KR_SERVICE_KEY", "wrong-key")
    bad_key = {"RESULT": {"CODE": "INFO-100", "MSG": "인증키가 유효하지 않습니다."}}
    xml = "<OpenAPI_ServiceResponse><returnAuthMsg>SERVICE_KEY_IS_NOT_REGISTERED_ERROR"
    _fake(monkeypatch, {"foodsafetykorea": bad_key, "apis.data.go.kr": xml})
    h = auth_headers

    by = _collect(client, h, _run(client, h))
    assert by["impfood_unfit"]["status"] == "failed"
    assert "INFO-100" in by["impfood_unfit"]["message"]
    assert by["mfds_notice"]["status"] == "failed"
    assert "JSON이 아님" in by["mfds_notice"]["message"]
    assert by["impfood_inspection"]["status"] == "manual"  # 나머지는 그대로 계속


def test_only_api_data_goes_to_server_db(
    client: TestClient, auth_headers: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    _api_mode(monkeypatch, {"impfood_unfit": UNFIT_MAP})
    monkeypatch.setenv("IMPFOOD_UNFIT_API", "I9999")
    monkeypatch.setenv("FOODSAFETY_API_KEY", "virtual-key")
    _fake(monkeypatch, {"openapi.foodsafetykorea.go.kr": FOODSAFETY_OK})
    sent: list[tuple[str, list[dict[str, Any]]]] = []

    def fake_upsert(table: str, rows: list[dict[str, Any]]) -> int:
        sent.append((table, rows))
        return len(rows)

    monkeypatch.setattr(public_db, "can_write", lambda: True)
    monkeypatch.setattr(public_db, "upsert", fake_upsert)
    h = auth_headers

    by = _collect(client, h, _run(client, h))
    assert "서버 DB 저장 1건" in by["impfood_unfit"]["message"]
    assert "서버 DB" not in by["mfds_notice"]["message"]  # API 아닌 출처는 올리지 않는다
    assert [(t, [r["source"] for r in rows]) for t, rows in sent] == [
        ("pub_source_item", ["impfood_unfit"])
    ]


def test_config_and_row_helpers(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("IMPFOOD_UNFIT_API", "I9999")
    assert api_client.config_for("impfood_unfit") is None  # 키가 없으면 수동 업로드
    monkeypatch.setenv("IMPFOOD_UNFIT_API_KEY", "own-key")
    cfg = api_client.config_for("impfood_unfit")
    assert cfg and cfg.style == "foodsafety" and cfg.key == "own-key"
    monkeypatch.delenv("IMPFOOD_UNFIT_API")
    from_json = api_client.config_for("impfood_unfit", {"api": {"service": "I8888"}})
    assert from_json and from_json.value == "I8888"  # 서비스 ID는 sources.json에 둘 수 있다

    assert api_client._find_rows({"body": {"items": {"item": {"A": "1"}}}}) == [{"A": "1"}]
    assert api_client.parse_date("2026.11.20 10:00") is not None
    row = api_client.to_row({"X_NM": "제목", "Y_DT": "20261120", "Z": ""}, {})
    assert row["title"] == "제목" and row["posted_at"] == "2026-11-20"
    assert row["fields"] == {"X_NM": "제목", "Y_DT": "20261120"}
