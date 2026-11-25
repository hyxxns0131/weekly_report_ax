"""B2-01 섹션 2 법령 개정: 항목 칸 / final 우선 / 해당 없음·재안내 / 담당자 확인용 (가상 샘플)."""

from datetime import date

from fastapi.testclient import TestClient

from app.b2_mail.input import load_selection
from app.b2_mail.report import section2_law as s2
from app.core.schema import Crosscheck, LawChange

EMPTY = "이번 주 새로 시행된 관련 법령 개정 사항은 해당 없습니다."
CHECK = "(담당자 확인용 · 발송 전 삭제)"


def _sample() -> tuple[list[LawChange], tuple[date, date]]:
    ws = load_selection(0, None, "sample")
    return ws.law_changes, (ws.period_start, ws.period_end)


def test_item_has_all_fields_from_input() -> None:
    changes, period = _sample()
    text = s2.render(changes, EMPTY, period=period)
    assert "「[가상] 수입식품등 검사 관련 고시」 일부개정 (가상 제2026-00호)" in text
    assert "공포·고시 2026-11-10 · 시행 2026-11-17" in text
    assert "주요 개정 조항: [가상] 제0조(검사 방법)" in text
    assert "관련 식품유형: 소스, 과자" in text
    assert "출처: https://example.com/sample/law/1" in text


def test_final_summary_first_and_unconfirmed_listed() -> None:
    changes, period = _sample()
    text = s2.render(changes, EMPTY, period=period)
    assert "주요 내용: [가상] 정밀검사 대상 품목을 넓히는 내용" in text
    assert "요약을 담당자가 아직 확인하지 않은 개정" in text.split(CHECK)[1]

    changes[0].final_summary = "담당자 수정 요약"
    text = s2.render(changes, EMPTY, period=period)
    assert "주요 내용: 담당자 수정 요약" in text
    assert CHECK not in text  # 확인할 것이 없으면 확인용 칸을 만들지 않는다


def test_blank_fields_and_window_and_mismatch() -> None:
    _, period = _sample()
    c = LawChange(id="law:x", crosscheck=Crosscheck.api_only, final_summary="요약")
    text = s2.render([c], EMPTY, period=period)
    assert "「확인 필요」 확인 필요 (확인 필요)" in text
    assert "공포·고시 확인 필요 · 시행 확인 필요" in text
    check = text.split(CHECK)[1]
    assert "대조 불일치 (1건)" in check
    assert "보고 기간 밖인 개정 (1건)" in check

    future = LawChange(id="law:y", effective_at=date(2027, 1, 1), final_summary="요약")
    assert "보고 기간 밖인 개정 (1건)" in s2.render([future], EMPTY, period=period)


def test_empty_week_and_reannounce() -> None:
    _, period = _sample()
    text = s2.render([], EMPTY, period=period)
    assert text.startswith(f"   {EMPTY}")
    assert "재안내 글을 입력해 주세요" in text

    text = s2.render([], EMPTY, reannounce="「가상 고시」 재안내 내용\n출처: 링크", period=period)
    assert EMPTY not in text
    assert "이전에 안내드린 개정 사항을 다시 안내드립니다." in text
    assert "   「가상 고시」 재안내 내용\n   출처: 링크" in text


def test_customer_mail_has_no_check_block() -> None:
    changes, _ = _sample()
    text = s2.render(changes, EMPTY)  # 고객사 메일은 period 없이 부른다
    assert CHECK not in text and "공포·고시 2026-11-10" in text
    assert s2.render([], EMPTY) == f"   {EMPTY}"


def test_reannounce_saved_and_used_in_report(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    h = auth_headers
    run_id = client.post("/api/core/runs", json={"reference_date": "2026-11-25"}, headers=h).json()[
        "id"
    ]
    res = client.put(
        f"/api/b2/runs/{run_id}/report/reannounce", json={"text": "재안내 테스트 글"}, headers=h
    )
    assert res.status_code == 200, res.text
    rep = client.post(f"/api/b2/runs/{run_id}/report?source=sample", headers=h).json()
    # 샘플에는 새 개정이 있으므로 재안내 글은 넣지 않고 확인용 칸에 알린다
    assert "재안내 테스트 글" not in rep["text"]
    assert "저장된 재안내 글이 있지만" in rep["text"]
