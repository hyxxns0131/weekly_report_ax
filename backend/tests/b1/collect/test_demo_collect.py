"""B1-02~06 데모 수집 (저장된 응답 읽기) + B1-09 열 이름표. 모든 자료는 가상이다."""

import json
from datetime import date
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.b1_select.collect import service
from app.b1_select.collect.base import load_demo
from app.b1_select.extract.table_mapper import map_row, split_tag

DEMO_SOURCES = [
    "impfood_unfit",
    "impfood_inspection",
    "impfood_law_policy",
    "mfds_notice",
    "gyeongin_newsletter",
]
START, END = date(2026, 11, 16), date(2026, 11, 22)


def _run(client: TestClient, h: dict[str, str]) -> int:
    res = client.post("/api/core/runs", json={"reference_date": "2026-11-25"}, headers=h)
    return int(res.json()["id"])


def test_demo_mode_collects_all_five(client: TestClient, auth_headers: dict[str, str]) -> None:
    h = auth_headers
    run_id = _run(client, h)
    res = client.post(f"/api/b1/runs/{run_id}/collect", json={"sources": DEMO_SOURCES}, headers=h)
    assert res.status_code == 200, res.text
    by = {r["source"]: r for r in res.json()}
    assert set(by) == set(DEMO_SOURCES)
    for sid in DEMO_SOURCES:
        assert by[sid]["status"] == "ok", by[sid]
        assert by[sid]["items"], sid
    assert len(by["impfood_unfit"]["items"]) == 6  # 7건 중 1건은 보고 기간 밖
    items = client.get(f"/api/b1/runs/{run_id}/items", headers=h).json()
    assert len(items) == 14

    # 다시 수집해도 같은 id는 한 번만 들어간다
    client.post(f"/api/b1/runs/{run_id}/collect", json={"sources": DEMO_SOURCES}, headers=h)
    assert len(client.get(f"/api/b1/runs/{run_id}/items", headers=h).json()) == 14


def test_missing_file_fails_only_that_source(
    client: TestClient, auth_headers: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    original = service.source_config()

    def broken() -> list[dict[str, Any]]:
        out = [dict(s) for s in original]
        for s in out:
            if s["id"] == "impfood_unfit":
                s["demo_file"] = "samples/b1_input/demo/없는_파일.json"
        return out

    monkeypatch.setattr(service, "source_config", broken)
    h = auth_headers
    run_id = _run(client, h)
    by = {
        r["source"]: r
        for r in client.post(
            f"/api/b1/runs/{run_id}/collect", json={"sources": DEMO_SOURCES}, headers=h
        ).json()
    }
    assert by["impfood_unfit"]["status"] == "failed"
    assert "데모 파일 없음" in by["impfood_unfit"]["message"]
    assert all(by[s]["status"] == "ok" for s in DEMO_SOURCES if s != "impfood_unfit")


def test_auto_mode_not_ready_is_failed(
    client: TestClient, auth_headers: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    original = service.source_config()
    monkeypatch.setattr(
        service,
        "source_config",
        lambda: [{**s, "mode": "auto"} if s["id"] == "mfds_notice" else s for s in original],
    )
    h = auth_headers
    run_id = _run(client, h)
    by = {
        r["source"]: r
        for r in client.post(
            f"/api/b1/runs/{run_id}/collect", json={"sources": DEMO_SOURCES}, headers=h
        ).json()
    }
    assert by["mfds_notice"]["status"] == "failed"
    assert "실제 수집기 준비 전" in by["mfds_notice"]["message"]
    assert by["impfood_unfit"]["status"] == "ok"


def _write(tmp_path: Path, rows: Any) -> Path:
    p = tmp_path / "demo.json"
    p.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    return p


def test_out_of_period_dropped_and_duplicates_once(tmp_path: Path) -> None:
    rows = [
        {"title": "가상 A", "posted_at": "2026-11-17", "body": "x"},
        {"title": "가상 A", "posted_at": "2026-11-17", "body": "x 중복"},
        {"title": "가상 B", "posted_at": "2026-11-01", "body": "기간 밖"},
        {"title": "가상 C", "posted_at": "2026-11-30", "body": "기간 밖"},
    ]
    r = load_demo("impfood_unfit", _write(tmp_path, rows), 1, START, END)
    assert r.status == "ok"
    assert [i.title for i in r.items] == ["가상 A"]
    assert "기간 밖 2건" in r.message


def test_zero_items_is_ok_with_warning(tmp_path: Path) -> None:
    r = load_demo("impfood_unfit", _write(tmp_path, []), 1, START, END)
    assert r.status == "ok" and not r.items
    assert "0건(구조 변경 의심)" in r.message


def test_bad_format_is_failed(tmp_path: Path) -> None:
    r = load_demo("impfood_unfit", _write(tmp_path, {"not": "a list"}), 1, START, END)
    assert r.status == "failed"
    r = load_demo("impfood_unfit", _write(tmp_path, [{"no_title": 1}]), 1, START, END)
    assert r.status == "failed"


def test_samc_columns_and_tag(tmp_path: Path) -> None:
    row = {
        "제조국가": "중국",
        "제조/수출회사": "Ocean Foods Co., Ltd.",
        "식품유형/품목명": "[가공식품] 냉동새우살",
        "부적합 사유": "대장균 기준 초과",
        "관련 화주": "A사",
    }
    got = map_row(row)
    assert got == {
        "origin_country": "중국",
        "maker": "Ocean Foods Co., Ltd.",
        "food_type_raw": "냉동새우살",
        "violation": "대장균 기준 초과",
    }
    assert map_row({"위반 내역": "메탄올 기준 초과"}) == {"violation": "메탄올 기준 초과"}
    assert split_tag("[가공식품] 냉동새우살") == ("냉동새우살", "가공식품")
    assert split_tag("냉동새우살") == ("냉동새우살", None)

    # 꼬리표는 본문에 "분류: …" 줄로 남는다
    p = _write(tmp_path, [{"title": "가상", "posted_at": "2026-11-17", "fields": row}])
    body = load_demo("impfood_unfit", p, 1, START, END).items[0].body
    assert "분류: 가공식품" in body
