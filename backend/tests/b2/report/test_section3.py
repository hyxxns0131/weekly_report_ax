"""B2-01 섹션 3 오늘의 팁: 근거가 있을 때만 넣기 / 담당자 확인용 / 고객사 메일 (가상 글)."""

from fastapi.testclient import TestClient

from app.b2_mail.report import section3_tip as s3

EMPTY = "이번 주 해당 없음."
CHECK = "(담당자 확인용 · 발송 전 삭제)"
GOOD = "가상 표시 조건 안내\n시험성적서를 함께 제출합니다.\n근거: 「가상 고시」 제1조 https://example.com/law/1"


def test_tip_with_basis_goes_in() -> None:
    text = s3.render(GOOD, EMPTY, staff=True)
    assert text.startswith("   매주 검역 관련하여 참고하시면 좋은 정보들을 안내 드립니다.")
    assert "   - 가상 표시 조건 안내\n     시험성적서를 함께 제출합니다.\n     근거:" in text
    assert CHECK not in text


def test_tip_without_link_or_basis_line_is_left_out() -> None:
    for tip in ("근거: 「가상 고시」 제1조", "가상 안내 https://example.com/law/1"):
        text = s3.render(tip, EMPTY, staff=True)
        assert text.startswith(f"   {EMPTY}")
        assert "가상" not in text.split(CHECK)[0]
        assert "근거(" in text.split(CHECK)[1]


def test_latest_marker_is_flagged() -> None:
    text = s3.render(GOOD + " · 최신본 확인 필요", EMPTY, staff=True)
    assert "가상 표시 조건 안내" in text.split(CHECK)[0]
    assert "최신본을 확인해 주세요" in text.split(CHECK)[1]


def test_no_tip() -> None:
    text = s3.render(None, EMPTY, staff=True)
    assert text.split("\n")[0] == f"   {EMPTY}"
    assert "SAMC 확인 필요" in text.split(CHECK)[1]  # 내부 메모는 확인용 칸에만


def test_customer_mail_has_no_check_block() -> None:
    assert s3.render(None, EMPTY) == f"   {EMPTY}"
    assert s3.render("근거 없는 팁", EMPTY) == f"   {EMPTY}"
    assert CHECK not in s3.render(GOOD, EMPTY) and "가상 표시 조건 안내" in s3.render(GOOD, EMPTY)


def test_saved_tip_used_in_report(client: TestClient, auth_headers: dict[str, str]) -> None:
    h = auth_headers
    run_id = client.post("/api/core/runs", json={"reference_date": "2026-11-25"}, headers=h).json()[
        "id"
    ]
    assert (
        client.put(f"/api/b2/runs/{run_id}/tip", json={"tip": GOOD}, headers=h).status_code == 200
    )
    rep = client.post(f"/api/b2/runs/{run_id}/report?source=sample", headers=h).json()
    assert "가상 표시 조건 안내" in rep["text"].split("3. ")[-1]
