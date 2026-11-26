"""B2-02 담당자용 메일: 실제 예시(11월 4주차) 머리말·맺음말, 확인 건수는 경고에만.

샘플 자료(가상 A사·B사)로 확인한다.
"""

from typing import Any

from fastapi.testclient import TestClient

from app.b2_mail.draft import staff
from app.b2_mail.draft.service import mail_config
from app.b2_mail.report.service import build


def _staff_draft(client: TestClient, h: dict[str, str]) -> tuple[int, dict[str, Any]]:
    run_id = client.post("/api/core/runs", json={"reference_date": "2026-11-25"}, headers=h).json()[
        "id"
    ]
    res = client.post(f"/api/b2/runs/{run_id}/drafts?source=sample", headers=h)
    assert res.status_code == 200, res.text
    drafts = [d for d in res.json() if d["kind"] == "staff_summary"]
    assert len(drafts) == 1
    return run_id, drafts[0]


def test_staff_body_follows_real_mail_layout(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    _, d = _staff_draft(client, auth_headers)
    body: str = d["ai_body"]
    # 주차 숫자는 core/period.py 결정에 따른다 (docs/b2/discussion_week_label.md)
    head = "수신자 제위\n\n안녕하세요.\nSAMC 통관검역1팀 담당자입니다.\n\n2026년 11월 "
    assert body.startswith(head)
    assert "주차 수입식품 검역 관련하여, 주요한 정보를 안내드립니다.\n\n1. 수입식품" in body
    assert body.endswith("\n\n감사합니다.")
    assert body.index("1. 수입식품") < body.index("2. 주간 법령 개정 소식")
    assert body.index("2. 주간 법령 개정 소식") < body.index("3. 주간 검역 정보 안내")


def test_check_counts_go_to_warnings_not_body(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    _, d = _staff_draft(client, auth_headers)
    assert "담당자 확인용" not in d["ai_body"]
    assert "검토 필요" not in d["ai_body"]
    assert "법령 대조 불일치" not in d["ai_body"]
    assert "검토 필요 1건 (보고서 확인 목록 참고, 메일에는 빠져 있음)" in d["warnings"]


def test_warnings_skip_zero_counts(client: TestClient, auth_headers: dict[str, str]) -> None:
    run_id, _ = _staff_draft(client, auth_headers)
    out, _ = build(run_id, None, "sample")
    cfg = mail_config()
    assert not any("법령 대조" in w for w in staff.warnings(out, 0, cfg))
    assert "법령 대조 불일치 2건 (법령 개정 화면에서 확인)" in staff.warnings(out, 2, cfg)
    out.review_needed = 0
    assert staff.warnings(out, 0, cfg) == []
