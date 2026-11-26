"""B2-02 경고: 링크 안 숫자는 '원문에 없는 숫자'로 잡지 않는다. 가상 샘플 자료로 확인한다."""

from fastapi.testclient import TestClient

from app.b2_mail.draft import checks
from app.b2_mail.report.service import build


def _run(client: TestClient, h: dict[str, str]) -> int:
    res = client.post("/api/core/runs", json={"reference_date": "2026-11-25"}, headers=h)
    run_id: int = res.json()["id"]
    return run_id


def test_staff_draft_has_no_number_warning_from_links(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    run_id = _run(client, auth_headers)
    res = client.post(f"/api/b2/runs/{run_id}/drafts?source=sample", headers=auth_headers)
    assert res.status_code == 200, res.text
    staff = next(d for d in res.json() if d["kind"] == "staff_summary")
    assert not any("원문에 없는 숫자" in w for w in staff["warnings"])


def test_made_up_number_outside_link_is_still_caught(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    run_id = _run(client, auth_headers)
    _, ws = build(run_id, None, "sample")
    found = checks.check("검출량 0.35 mg/kg https://example.com/A01B02", ws, [])
    assert "원문에 없는 숫자: 0.35" in found
    assert not any("01" in w or "02" in w for w in found)
