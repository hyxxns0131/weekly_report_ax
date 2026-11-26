"""B2-01 섹션 1: 고객사 관련 본문 / 담당자 확인용 / 고객사 메일 (샘플, 가상 A사·B사)."""

from app.b2_mail.input import load_customer_names, load_selection
from app.b2_mail.report import section1_unfit as s1
from app.core.schema import Confidence, Label, SelectedItem

EMPTY = "이번 주 해당 없음."


def _sample() -> tuple[list[SelectedItem], dict[str, str]]:
    return load_selection(0, None, "sample").items, load_customer_names(None, "sample")


def _item(items: list[SelectedItem], key: str) -> SelectedItem:
    return next(i for i in items if i.raw.id.endswith(key))


def _both(items: list[SelectedItem], names: dict[str, str]) -> tuple[str, str]:
    """(본문, 담당자 확인 목록)."""
    picked = s1.pick(items)
    body = s1.render(picked, names, EMPTY)
    check = "\n".join(s1.check_lines(picked, names, s1.pick_review(items)))
    return body, check


def test_staff_body_has_related_only_and_same_maker_first() -> None:
    items, names = _sample()
    body, _ = _both(items, names)
    assert "■ 우리 고객사 관련 부적합 (2건)" in body
    assert body.index("샘플 위스키") < body.index("샘플 레드와인")  # 같은 제조사 건이 먼저
    # 실제 메일처럼 표 모양: 머리줄 + 한 건 한 줄
    assert (
        "| 부적합일자 | 제조국가 | 제조/수출회사 | 식품유형/품목명 | 위반 내역 | 관련 화주 | 출처 |"
        in body
    )
    assert (
        "| 2026-11-17 | 영국 | 가상 증류소 X | [위스키] 샘플 위스키 12년(Sample Whisky 12Y)"
        " | 메탄올 기준 초과 (가상 값) | A사 【같은 제조사】 | https://example.com/sample/unfit/1 |"
    ) in body
    assert "수입 이력:" not in body and "키워드)" not in body  # 관련 화주는 이름만, 근거 문장 없음
    assert "■ 통관단계 검사지시 안내 (1건)" in body
    assert "샘플 쌀과자" not in body  # 검토 필요 항목은 본문에 넣지 않는다


def test_inspection_is_ga_na_da_block() -> None:
    """통관단계 검사지시: 실제 메일처럼 # 제목 / 가. 나. 다. (고객사 메일은 관련화주 없이)."""
    items, names = _sample()
    body = s1.render(s1.pick(items), names, EMPTY)
    assert (
        "   # [가상] 통관단계 검사지시\n"
        "     가. 검사기간 : 2026-11-20 ~ 2027-02-19\n"
        "     나. 관련화주 : B사\n"
        "     다. 대상 품목 및 검사항목 : 태국 / 소스 / 확인 필요\n"
        "     출처: https://example.com/sample/inspection/1"
    ) in body
    mine = [i for i in s1.pick(items) if "C002" in s1.matched_ids(i)]
    mail = s1.render(mine, names, EMPTY, show_customers=False)
    assert "관련화주" not in mail and "     나. 대상 품목 및 검사항목 : 태국 / 소스" in mail


def test_review_items_listed_in_check_block() -> None:
    items, names = _sample()
    _, check = _both(items, names)
    assert "■ 검토 필요 · 선별 확인 후 반영 (1건)" in check
    assert "샘플 쌀과자 / 사유: 식품유형은 맞지만" in check


def test_blank_fields_show_check_needed() -> None:
    items, names = _sample()
    text = s1.render(s1.pick(items), names, EMPTY)
    insp = next(ln for ln in text.splitlines() if "대상 품목 및 검사항목" in ln)
    assert insp.endswith("태국 / 소스 / 확인 필요")  # 검사항목(원문에 없음) → 확인 필요


def test_name_falls_back_to_title_then_check_needed() -> None:
    """이름 자리: 제품명 → (없으면) 원문 제목 → (둘 다 없으면) "확인 필요"."""
    items, _ = _sample()
    item = _item(items, "inspection-1")
    assert item.extracted is not None

    item.extracted.food_type_std = item.extracted.food_type_raw = None
    assert s1._product(item) == "[가상] 통관단계 검사지시"  # 식품유형도 없는 안내문: 제목만

    item.raw.title = ""
    assert s1._product(item) == "확인 필요"

    item.extracted.product_name_ko = "가상 칠리소스"  # 제품명은 있고 식품유형만 없음
    assert s1._product(item) == "[확인 필요] 가상 칠리소스"


def test_final_values_override_ai() -> None:
    items, names = _sample()
    whisky = _item(items, "unfit-1")
    whisky.matches[0].final_matched = False  # 담당자가 A사 관련을 지움
    rice = _item(items, "unfit-3")
    rice.selection.final_label = Label.relevant  # 담당자가 검토 필요 → 관련으로 확정
    rice.matches[0].final_matched = True  # b1 고객사 판단 화면에서 B사 [유지]
    body, check = _both(items, names)
    assert "[과자] 샘플 쌀과자 | 산가 기준 초과 (가상 값) | B사 |" in body
    assert "샘플 위스키" in check and "■ 고객사와 맞지 않은 부적합 (1건)" in check
    assert "■ 검토 필요" not in check


def test_unconfirmed_medium_match_stays_out_of_body() -> None:
    """확인 전 + 신뢰도 중간 판단은 본문에 넣지 않고 확인 목록에서 [유지]/[제외]를 안내한다."""
    items, names = _sample()
    rice = _item(items, "unfit-3")  # B사: 원산지+식품유형 일치지만 신뢰도 중간, 담당자 확인 전
    rice.selection.final_label = Label.relevant
    body, check = _both(items, names)
    assert "샘플 쌀과자" not in body
    assert "■ 고객사 판단 확인 전 · 고객사 판단 화면(/customers)에서 [유지] 또는 [제외]" in check
    assert "샘플 쌀과자 / 확인 전 후보: B사 (" in check
    assert (
        "고객사와 맞지 않은" not in check.split("샘플 쌀과자")[0]
    )  # 후보가 있으니 '맞지 않음' 아님

    rice.matches[0].final_matched = False  # 담당자 [제외] → 본문에도 후보에도 없다
    body, check = _both(items, names)
    assert "샘플 쌀과자" not in body and "확인 전 후보" not in check


def test_confirmed_and_pending_on_same_item() -> None:
    """한 건에 확정 고객사와 확인 전 후보가 같이 있으면: 본문에는 확정만, 후보는 확인 목록에."""
    items, names = _sample()
    wine = _item(items, "unfit-2")  # A사: 신뢰도 높음
    extra = wine.matches[0].model_copy(
        update={"customer_id": "C002", "confidence": Confidence.medium, "reason": "가상 후보"}
    )
    wine.matches.append(extra)
    body, check = _both(items, names)
    wine_line = next(ln for ln in body.splitlines() if "샘플 레드와인" in ln)
    assert "| A사 |" in wine_line and "B사" not in wine_line
    assert "샘플 레드와인(Sample Red Wine) / 확인 전 후보: B사 (가상 후보)" in check


def test_empty_week_keeps_frame() -> None:
    text = s1.render([], {}, EMPTY)
    assert "■ 우리 고객사 관련 부적합 (0건)\n     이번 주 해당 없음." in text
    assert "■ 통관단계 검사지시 안내 (0건)\n     이번 주 해당 없음." in text
    assert s1.check_lines([], {}, []) == []


def test_customer_mail_has_no_customer_names_or_check_block() -> None:
    items, names = _sample()
    mine = [i for i in s1.pick(items) if "C001" in s1.matched_ids(i)]
    text = s1.render(mine, names, "귀사 해당 없음", show_customers=False)
    assert "샘플 위스키" in text and "샘플 레드와인" in text
    assert "A사" not in text and "관련 화주" not in text
    assert s1.render([], names, "귀사 해당 없음", show_customers=False) == "  귀사 해당 없음"
