"""B2-01 섹션 1: 고객사 관련 본문 / 담당자 확인용 / 고객사 메일 (샘플, 가상 A사·B사)."""

from app.b2_mail.input import load_customer_names, load_selection
from app.b2_mail.report import section1_unfit as s1
from app.core.schema import Label, SelectedItem

EMPTY = "이번 주 해당 없음."


def _sample() -> tuple[list[SelectedItem], dict[str, str]]:
    return load_selection(0, None, "sample").items, load_customer_names(None, "sample")


def _item(items: list[SelectedItem], key: str) -> SelectedItem:
    return next(i for i in items if i.raw.id.endswith(key))


def _staff_body(text: str) -> str:
    """담당자 확인용 칸 앞까지 (발송되는 본문)."""
    return text.split("(담당자 확인용")[0]


def test_staff_body_has_related_only_and_same_maker_first() -> None:
    items, names = _sample()
    text = s1.render(s1.pick(items), names, EMPTY, review=s1.pick_review(items))
    body = _staff_body(text)
    assert "■ 우리 고객사 관련 부적합 (2건)" in body
    assert body.index("샘플 위스키") < body.index("샘플 레드와인")  # 같은 제조사 건이 먼저
    assert "【같은 제조사】 [2026-11-17] 영국 / 가상 증류소 X / [위스키]" in body
    assert "관련 화주: A사 (같은 제조사 수입 이력" in body
    assert "■ 통관단계 검사지시 안내 (1건)" in body
    assert "출처: https://example.com/sample/unfit/1" in body
    assert "샘플 쌀과자" not in body  # 검토 필요 항목은 본문에 넣지 않는다


def test_review_items_listed_in_check_block() -> None:
    items, names = _sample()
    text = s1.render(s1.pick(items), names, EMPTY, review=s1.pick_review(items))
    check = text.split("(담당자 확인용 · 발송 전 삭제)")[1]
    assert "■ 검토 필요 · 선별 확인 후 반영 (1건)" in check
    assert "샘플 쌀과자 / 사유: 식품유형은 맞지만" in check


def test_blank_fields_show_check_needed() -> None:
    items, names = _sample()
    text = s1.render(s1.pick(items), names, EMPTY)
    insp = next(ln for ln in text.splitlines() if "태국" in ln)
    assert "[소스] 확인 필요" in insp  # 제품명 없음
    assert "검사 항목: 확인 필요" in insp


def test_final_values_override_ai() -> None:
    items, names = _sample()
    whisky = _item(items, "unfit-1")
    whisky.matches[0].final_matched = False  # 담당자가 A사 관련을 지움
    rice = _item(items, "unfit-3")
    rice.selection.final_label = Label.relevant  # 담당자가 검토 필요 → 관련으로 확정
    text = s1.render(s1.pick(items), names, EMPTY, review=s1.pick_review(items))
    body, check = text.split("(담당자 확인용 · 발송 전 삭제)")
    assert "샘플 쌀과자" in body and "관련 화주: B사" in body
    assert "샘플 위스키" in check and "■ 고객사와 맞지 않은 부적합 (1건)" in check
    assert "■ 검토 필요" not in check


def test_empty_week_keeps_frame() -> None:
    text = s1.render([], {}, EMPTY)
    assert "■ 우리 고객사 관련 부적합 (0건)\n     이번 주 해당 없음." in text
    assert "■ 통관단계 검사지시 안내 (0건)\n     이번 주 해당 없음." in text
    assert "담당자 확인용" not in text


def test_customer_mail_has_no_customer_names_or_check_block() -> None:
    items, names = _sample()
    mine = [i for i in s1.pick(items) if "C001" in s1.matched_ids(i)]
    text = s1.render(mine, names, "귀사 해당 없음", show_customers=False)
    assert "샘플 위스키" in text and "샘플 레드와인" in text
    assert "A사" not in text and "관련 화주" not in text and "담당자 확인용" not in text
    assert s1.render([], names, "귀사 해당 없음", show_customers=False) == "  귀사 해당 없음"
