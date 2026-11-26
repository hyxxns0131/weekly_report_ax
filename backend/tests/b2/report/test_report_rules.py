"""B2-01 보고서 약속 확인 (5단계): 전체가 빈 주, 담당자 값(final_*) 우선, 빈 칸, 다시 조립.

모두 가상 자료(samples/b1_output/sample_week.json, 가상 A사·B사)만 쓴다.
보고서는 service.build()로 조립하고, b1 결과는 load_selection을 바꿔 끼워 넣는다.
"""

from collections.abc import Callable
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from app.b2_mail.draft import customer
from app.b2_mail.input import load_selection
from app.b2_mail.report import service
from app.core.schema import (
    Category,
    Confidence,
    CustomerMatch,
    Label,
    MatchRule,
    RawItem,
    SelectedItem,
    Selection,
    Source,
    WeeklySelection,
)

Build = Callable[[WeeklySelection], service.ReportOut]


def _sample() -> WeeklySelection:
    return load_selection(0, None, "sample")


def _item(ws: WeeklySelection, key: str) -> SelectedItem:
    return next(i for i in ws.items if i.raw.id.endswith(key))


def _section1(text: str) -> str:
    return text.split("2. 주간 법령 개정 소식")[0]


@pytest.fixture
def build(
    client: TestClient, auth_headers: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> Build:
    """주어진 b1 결과(WeeklySelection)로 보고서를 조립한다 (임시 DB의 새 주간 실행)."""
    run_id = client.post(
        "/api/core/runs", json={"reference_date": "2026-11-25"}, headers=auth_headers
    ).json()["id"]

    def _build(ws: WeeklySelection) -> service.ReportOut:
        monkeypatch.setattr(service, "load_selection", lambda *_a, **_k: ws)
        out, _ = service.build(run_id, None, "sample")
        return out

    return _build


def test_whole_empty_week_keeps_three_sections(build: Build) -> None:
    """1. 항목·법령·팁이 모두 없는 주: 섹션 1·2·3 틀은 그대로, 내용은 모두 "해당 없음"."""
    ws = _sample()
    ws.items, ws.law_changes = [], []
    out = build(ws)
    body = out.text
    assert body.startswith("1. 수입식품 부적합·통관단계 검사지시 (부적합일자 : 11/16~11/22)\n")
    assert "■ 우리 고객사 관련 부적합 (0건)\n     이번 주 해당 없음." in body
    assert "■ 통관단계 검사지시 안내 (0건)\n     이번 주 해당 없음." in body
    assert (
        "2. 주간 법령 개정 소식\n   이번 주 새로 시행된 관련 법령 개정 사항은 해당 없습니다."
        in body
    )
    assert "3. 주간 검역 정보 안내\n   이번 주 해당 없음." in body
    tail = out.check  # 화면 전용 확인 목록
    assert "재안내 글을 입력해 주세요" in tail and "이번 주 팁이 없어요" in tail


def test_item_marked_irrelevant_by_staff_disappears(build: Build) -> None:
    """2. AI는 '관련', 담당자는 '무관' → 본문에도 확인용 칸에도 없다."""
    ws = _sample()
    _item(ws, "unfit-1").selection.final_label = Label.irrelevant
    out = build(ws)
    assert "샘플 위스키" not in out.text and "샘플 위스키" not in out.check
    assert "■ 우리 고객사 관련 부적합 (1건)" in out.text


def test_category_changed_by_staff_moves_group(build: Build) -> None:
    """3. AI는 '부적합', 담당자는 '검사지시' → 검사지시 묶음으로 옮겨 간다."""
    ws = _sample()
    _item(ws, "unfit-2").selection.final_category = Category.inspection_order
    s1 = _section1(build(ws).text)
    assert "■ 우리 고객사 관련 부적합 (1건)" in s1
    assert "■ 통관단계 검사지시 안내 (2건)" in s1
    assert s1.index("■ 통관단계 검사지시 안내") < s1.index("# [가상] 과실주 부적합")


def test_customer_added_by_staff_goes_to_body_and_mail(build: Build) -> None:
    """4. AI는 관련 없음, 담당자가 B사를 '관련'으로 추가 → 본문과 B사 메일에 들어간다."""
    ws = _sample()
    wine = _item(ws, "unfit-2")
    wine.matches.append(
        CustomerMatch(
            item_id=wine.raw.id,
            customer_id="C002",
            ai_matched=False,
            final_matched=True,
            rule=MatchRule.food_type_only,
            confidence=Confidence.medium,
            reason="담당자 추가",
        )
    )
    out = build(ws)
    assert "| A사, B사 |" in out.text  # 관련 화주 칸: 이름만
    assert "담당자 추가" not in out.text  # 판단 근거 문장은 메일 글에 넣지 않는다
    assert "샘플 레드와인" in customer.body(out, "C002")


def test_item_without_extracted_info_shows_check_needed(build: Build) -> None:
    """5. 추출 정보·날짜·링크가 모두 없는 항목도 오류 없이 제목 + "확인 필요"로 나온다."""
    ws = _sample()
    ws.items.append(
        SelectedItem(
            raw=RawItem(
                id="manual:bare",
                run_id=ws.run_id,
                source=Source.manual,
                title="[가상] 추출 전 부적합 공지",
                body="",
                collected_at=datetime(2026, 11, 20, 9, 0),
            ),
            selection=Selection(
                item_id="manual:bare", ai_label=Label.relevant, ai_category=Category.unfit
            ),
        )
    )
    tail = build(ws).check  # 고객사와 맞지 않아 확인 목록으로 간다
    assert "■ 고객사와 맞지 않은 부적합 (1건)" in tail
    assert "[확인 필요] [가상] 추출 전 부적합 공지 / 관련 화주: 없음" in tail
    assert "출처: 확인 필요" in tail


def test_rebuild_keeps_saved_tip_and_reannounce(build: Build) -> None:
    """6. 팁·재안내 글을 저장한 뒤 보고서를 두 번 만들어도 저장값이 지워지지 않는다."""
    ws = _sample()
    ws.law_changes = []
    run_id = build(ws).report.run_id
    tip = "가상 안내\n근거: 「가상 고시」 제1조 https://example.com/law/1"
    service.set_tip(run_id, tip)
    service.set_reannounce(run_id, "「가상 고시」 재안내 글")
    for _ in range(2):
        out = build(ws)
    assert out.report.section3_tip == tip
    assert "   - 가상 안내" in out.text
    assert "「가상 고시」 재안내 글" in out.text
