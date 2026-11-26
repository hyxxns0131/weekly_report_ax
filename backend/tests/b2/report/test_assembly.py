"""B2-01 조립: 섹션 이름·기간, 확인 목록은 check 칸에만(메일 글·메일 초안에 없음), 샘플."""

from fastapi.testclient import TestClient

from app.b2_mail.draft import customer, staff
from app.b2_mail.report.service import build

# 확인 목록에만 나오는 글자들. 메일로 나가는 글에 하나라도 있으면 안 된다.
CHECK_WORDS = ("[1. 부적합·검사지시]", "[2. 법령 개정]", "[3. 검역 정보 안내]", "검토 필요 · 선별")


def _report(client: TestClient, h: dict[str, str]) -> tuple[int, dict[str, str]]:
    run_id = client.post("/api/core/runs", json={"reference_date": "2026-11-25"}, headers=h).json()[
        "id"
    ]
    rep = client.post(f"/api/b2/runs/{run_id}/report?source=sample", headers=h)
    assert rep.status_code == 200, rep.text
    return run_id, rep.json()


def test_text_is_mail_body_only_and_check_is_separate(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    _, rep = _report(client, auth_headers)
    text, check = rep["text"], rep["check"]
    assert text.startswith("1. 수입식품 부적합·통관단계 검사지시 (부적합일자 : 11/16~11/22)\n")
    assert text.index("2. 주간 법령 개정 소식\n") < text.index("3. 주간 검역 정보 안내\n")
    assert not any(w in text for w in CHECK_WORDS)  # 메일 글에는 확인 목록이 없다
    assert "담당자 확인용" not in text and "발송 전 삭제" not in text
    assert "샘플 쌀과자" not in text  # 검토 필요 항목은 메일 글에 없다

    assert " [1. 부적합·검사지시]" in check and "샘플 쌀과자" in check
    assert " [2. 법령 개정]" in check and "요약을 담당자가 아직 확인하지 않은 개정" in check
    assert " [3. 검역 정보 안내]" in check and "이번 주 팁이 없어요" in check


def test_mail_drafts_have_no_check_list(client: TestClient, auth_headers: dict[str, str]) -> None:
    run_id, _ = _report(client, auth_headers)
    out, _ = build(run_id, None, "sample")
    for body in (staff.body(out, 0), customer.body(out, "C001"), customer.body(out, "C002")):
        assert not any(w in body for w in CHECK_WORDS)
        assert "샘플 쌀과자" not in body  # 검토 필요 항목은 어떤 메일에도 없다
    a = customer.body(out, "C001")
    assert "B사" not in a and "2. 주간 법령 개정 소식" in a and "부적합일자" not in a
