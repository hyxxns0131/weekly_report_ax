"""섹션 1 부적합·통관단계 검사지시 (DESIGN.md 10-1, 실제 예시 11월 4주차 형식).

- 본문: 고객사 관련 부적합 + 고객사 관련 통관단계 검사지시. 같은 제조사 건을 맨 위에 둔다.
- 담당자 확인용(발송 전 삭제): 고객사와 맞지 않은 부적합·검사지시, 그 밖의 관련 소식, 검토 필요.
- 숫자·날짜는 입력 값만 쓰고, 빈 칸은 "확인 필요". 판단 값은 final_*가 있으면 그것을 쓴다.
- 문구는 config/b2/report.json의 "section1"에만 둔다.
"""

from typing import Any

from app.core.schema import Category, CustomerMatch, Label, MatchRule, SelectedItem

UNFIT = {Category.unfit}
INSPECTION = {Category.inspection_order}
MISSING = "확인 필요"


def label_of(item: SelectedItem) -> Label:
    return item.selection.final_label or item.selection.ai_label


def category_of(item: SelectedItem) -> Category:
    return item.selection.final_category or item.selection.ai_category


def _matched(m: CustomerMatch) -> bool:
    return m.final_matched if m.final_matched is not None else m.ai_matched


def matched_ids(item: SelectedItem) -> list[str]:
    return [m.customer_id for m in item.matches if _matched(m)]


def pick(items: list[SelectedItem]) -> list[SelectedItem]:
    """보고서 섹션 1: 선별이 '관련'인 부적합·검사지시·기타 관련 소식."""
    return [
        i for i in items if label_of(i) == Label.relevant and category_of(i) != Category.law_change
    ]


def pick_review(items: list[SelectedItem]) -> list[SelectedItem]:
    """담당자 확인용: 선별이 '검토 필요'인 항목 (법령 개정은 섹션 2에서 다룬다)."""
    return [
        i
        for i in items
        if label_of(i) == Label.review_needed and category_of(i) != Category.law_change
    ]


def same_maker(item: SelectedItem) -> bool:
    """고객사 수입 이력과 제조사가 같은 건 (RULES.md 11-2 순서 1). 강조해서 맨 위에 둔다."""
    return any(_matched(m) and m.rule == MatchRule.maker for m in item.matches)


def _v(x: object) -> str:
    return str(x) if x not in (None, "") else MISSING


def _text() -> dict[str, Any]:
    from app.b2_mail.report.service import config  # service가 이 모듈을 import하므로 늦게 부른다

    data: dict[str, Any] = config()["section1"]
    return data


def _product(item: SelectedItem) -> str:
    e = item.extracted
    if e is None:
        return item.raw.title or MISSING
    food = _v(e.food_type_std or e.food_type_raw)
    name = _v(e.product_name_ko) + (f"({e.product_name_en})" if e.product_name_en else "")
    return f"[{food}] {name}"


def _customers(item: SelectedItem, names: dict[str, str]) -> str:
    found = [m for m in item.matches if _matched(m)]
    if not found:
        return "없음"
    return " / ".join(f"{names.get(m.customer_id, m.customer_id)} ({m.reason})" for m in found)


def line(item: SelectedItem, names: dict[str, str], show_customers: bool) -> str:
    """항목 한 줄. 부적합: 제조국가 / 제조·수출회사 / [식품유형] 품목명 / 위반 내역."""
    t = _text()
    e = item.extracted
    mark = t["same_maker_mark"] + " " if show_customers and same_maker(item) else ""
    head = f"   - {mark}[{_v(item.raw.posted_at)}] "
    cat = category_of(item)
    if e and cat in UNFIT:
        parts = [_v(e.origin_country), _v(e.maker), _product(item), f"위반 내역: {_v(e.violation)}"]
    elif e and cat in INSPECTION:
        parts = [
            _v(e.origin_country),
            _product(item),
            f"검사 항목: {_v(e.violation)}",
            f"검사 기간: {_v(e.period_start)}~{_v(e.period_end)}",
        ]
    else:
        parts = [item.raw.title or MISSING]
    if show_customers:
        parts.append(f"관련 화주: {_customers(item, names)}")
    return head + " / ".join(parts) + f"\n     출처: {_v(item.raw.url)}"


def _review_line(item: SelectedItem) -> str:
    reason = item.selection.ai_reason or MISSING
    return (
        f"   - [{_v(item.raw.posted_at)}] {_product(item)} / 사유: {reason}"
        f"\n     출처: {_v(item.raw.url)}"
    )


def _group(title: str, lines: list[str], empty: str | None) -> list[str]:
    """■ 제목 (N건) + 줄들. 비었을 때 empty가 있으면 그 문구를, 없으면 묶음을 통째로 뺀다."""
    if not lines and empty is None:
        return []
    return [f"  ■ {title} ({len(lines)}건)", *(lines or [f"     {empty}"])]


def _sorted(items: list[SelectedItem]) -> list[SelectedItem]:
    return sorted(items, key=lambda i: not same_maker(i))  # 같은 제조사 건이 먼저


def render(
    items: list[SelectedItem],
    names: dict[str, str],
    empty: str,
    show_customers: bool = True,
    review: list[SelectedItem] | None = None,
) -> str:
    """show_customers=True: 담당자용(본문 + 담당자 확인용). False: 고객사 메일(그 고객사 항목만)."""
    t = _text()
    unfit = [i for i in items if category_of(i) in UNFIT]
    insp = [i for i in items if category_of(i) in INSPECTION]
    other = [i for i in items if i not in unfit and i not in insp]

    if not show_customers:
        if not items:
            return f"  {empty}"
        out: list[str] = []
        out += _group(t["group_unfit"], [line(i, names, False) for i in unfit], None)
        out += _group(t["group_inspection"], [line(i, names, False) for i in insp], None)
        out += _group(t["group_other"], [line(i, names, False) for i in other], None)
        return "\n".join(out)

    related_unfit = _sorted([i for i in unfit if matched_ids(i)])
    related_insp = _sorted([i for i in insp if matched_ids(i)])
    no_unfit = [i for i in unfit if not matched_ids(i)]
    no_insp = [i for i in insp if not matched_ids(i)]
    review = review or []
    group_empty = empty  # 매주 같은 틀: 본문 묶음은 비어도 남기고 "해당 없음"을 넣는다

    out = [f"  {s}" for s in t["intro"]]
    out.append(f"  {t['source_unfit']}")
    out += _group(t["group_related"], [line(i, names, True) for i in related_unfit], group_empty)
    out.append(f"  {t['source_inspection']}")
    out += _group(t["group_inspection"], [line(i, names, True) for i in related_insp], group_empty)

    check: list[str] = []
    check += _group(t["group_unmatched_unfit"], [line(i, names, True) for i in no_unfit], None)
    check += _group(t["group_unmatched_inspection"], [line(i, names, True) for i in no_insp], None)
    check += _group(t["group_other"], [line(i, names, True) for i in other], None)
    check += _group(t["group_review"], [_review_line(i) for i in review], None)
    if check:
        out += ["", f"  {t['check_title']}", *check]
    return "\n".join(out)
