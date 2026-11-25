"""B1-01 → B1-08 → B1-09 → B1-11: CSV 업로드부터 고객사 판단까지 (가상 자료)."""

from fastapi.testclient import TestClient

CSV = (
    "부적합일자,제품명,식품유형,제조국,제조업소,위반내역,링크\n"
    "2026-11-17,테스트 위스키,위스키,영국,가상 증류소 X,메탄올 기준 초과,https://example.com/1\n"
    "2026-11-18,테스트 쌀과자,과자,베트남,가상 제과 W,산가 기준 초과,https://example.com/2\n"
)


def _run(client: TestClient, h: dict[str, str]) -> int:
    return client.post("/api/core/runs", json={"reference_date": "2026-11-25"}, headers=h).json()[
        "id"
    ]


def test_upload_analyze_match(client: TestClient, auth_headers: dict[str, str]) -> None:
    h = auth_headers
    run_id = _run(client, h)
    up = client.post(
        f"/api/b1/runs/{run_id}/upload",
        json={"source": "impfood_unfit", "kind": "csv", "content": "﻿" + CSV},
        headers=h,
    )
    assert up.status_code == 200, up.text
    assert len(up.json()["items"]) == 2

    res = client.post(f"/api/b1/runs/{run_id}/analyze", headers=h).json()
    assert res["total"] == 2 and res["relevant"] == 2

    items = client.get(f"/api/b1/runs/{run_id}/items", headers=h).json()
    whisky = next(i for i in items if "위스키" in i["raw"]["title"])
    assert whisky["extracted"]["maker"] == "가상 증류소 X"
    assert whisky["selection"]["ai_category"] == "unfit"

    matches = client.get(f"/api/b1/runs/{run_id}/matches", headers=h).json()
    by = {(m["customer_name"], m["rule"]) for m in matches}
    assert ("A사", "maker") in by
    assert ("B사", "origin_food_type") in by

    # 담당자가 무관으로 바꾸면 그 항목의 AI 판단이 빠진다
    item_id = whisky["raw"]["id"]
    p = client.patch(
        f"/api/b1/items/{item_id}/selection", json={"final_label": "irrelevant"}, headers=h
    )
    assert p.json()["reviewed_by"] == "test_admin"
    matches = client.get(f"/api/b1/runs/{run_id}/matches", headers=h).json()
    assert all(m["item_id"] != item_id for m in matches)


def test_extracted_edit_kept_on_reanalyze(client: TestClient, auth_headers: dict[str, str]) -> None:
    h = auth_headers
    run_id = _run(client, h)
    client.post(f"/api/b1/runs/{run_id}/upload", json={"kind": "csv", "content": CSV}, headers=h)
    client.post(f"/api/b1/runs/{run_id}/analyze", headers=h)
    item_id = client.get(f"/api/b1/runs/{run_id}/items", headers=h).json()[0]["raw"]["id"]
    client.patch(f"/api/b1/items/{item_id}/extracted", json={"origin_country": "프랑스"}, headers=h)
    client.post(f"/api/b1/runs/{run_id}/analyze", headers=h)
    got = next(
        i
        for i in client.get(f"/api/b1/runs/{run_id}/items", headers=h).json()
        if i["raw"]["id"] == item_id
    )
    assert got["extracted"]["origin_country"] == "프랑스"
    assert "origin_country" in got["extracted"]["edited_fields"]


def test_excel_is_refused(client: TestClient, auth_headers: dict[str, str]) -> None:
    run_id = _run(client, auth_headers)
    res = client.post(
        f"/api/b1/runs/{run_id}/upload",
        json={"kind": "csv", "content": "x", "filename": "a.xlsx"},
        headers=auth_headers,
    )
    assert res.status_code == 415
