"""B2-01 조립: 섹션 이름·기간, 담당자 확인용은 맨 끝 한 곳, 고객사 메일에는 확인용 없음 (샘플)."""

from fastapi.testclient import TestClient

CHECK = "(담당자 확인용 · 발송 전 삭제)"


def _report(client: TestClient, h: dict[str, str]) -> tuple[int, str]:
    run_id = client.post("/api/core/runs", json={"reference_date": "2026-11-25"}, headers=h).json()[
        "id"
    ]
    rep = client.post(f"/api/b2/runs/{run_id}/report?source=sample", headers=h)
    assert rep.status_code == 200, rep.text
    return run_id, rep.json()["text"]


def test_titles_and_single_check_block_at_end(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    _, text = _report(client, auth_headers)
    assert text.startswith("1. 수입식품 부적합·통관단계 검사지시 (부적합일자 : 11/16~11/22)\n")
    s2 = text.index("2. 주간 법령 개정 소식\n")
    s3 = text.index("3. 주간 검역 정보 안내\n")
    assert text.count(CHECK) == 1  # 확인용 칸은 한 곳뿐
    check_at = text.index(CHECK)
    assert check_at > s3 > s2  # 맨 끝
    tail = text[check_at:]
    assert " [1. 부적합·검사지시]" in tail and "샘플 쌀과자" in tail
    assert " [2. 법령 개정]" in tail and "요약을 담당자가 아직 확인하지 않은 개정" in tail
    assert " [3. 검역 정보 안내]" in tail and "이번 주 팁이 없어요" in tail
    assert "샘플 쌀과자" not in text[:check_at]  # 검토 필요 항목은 본문에 없음


def test_customer_mail_has_no_check_block(client: TestClient, auth_headers: dict[str, str]) -> None:
    from app.b2_mail.draft import customer
    from app.b2_mail.report.service import build

    run_id, _ = _report(client, auth_headers)
    out, _ = build(run_id, None, "sample")
    body = customer.body(out, "C001")
    assert CHECK not in body and "B사" not in body
    assert "2. 주간 법령 개정 소식" in body and "부적합일자" not in body
