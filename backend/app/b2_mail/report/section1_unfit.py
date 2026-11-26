"""섹션 1 부적합·통관단계 검사지시 (DESIGN.md 10-1, 실제 예시 11월 4주차 형식).

- 본문: 고객사 관련 부적합 + 고객사 관련 통관단계 검사지시. 같은 제조사 건을 맨 위에 둔다.
  "관련 화주"에는 확정된 판단만 넣는다: 담당자가 b1에서 [유지]한 것(final_matched=True),
  또는 담당자 확인 전이라도 신뢰도 높음(같은 제조사·HS·원산지+식품유형).
  확인 전 + 신뢰도 중간(식품유형만 일치 등, RULES.md 11-2 "검토 필요")은 본문에 넣지 않는다.
- 화면 전용 확인 목록(check_lines): 고객사 판단 확인 전 후보, 고객사와 맞지 않은
  부적합·검사지시, 그 밖의 관련 소식, 검토 필요. 메일 글에는 들어가지 않는다.
- 숫자·날짜는 입력 값만 쓰고, 빈 칸은 "확인 필요". 판단 값은 final_*가 있으면 그것을 쓴다.
- 문구는 config/b2/report.json의 "section1"에만 둔다.
"""

from typing import Any

from app.core.schema import Category, Confidence, CustomerMatch, Label, MatchRule, SelectedItem

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
    """AI 또는 담당자 기준 '관련'인 고객사 (확인 전 후보 포함). 고객사 메일·검증이 쓴다."""
    return [m.customer_id for m in item.matches if _matched(m)]


def _confirmed(m: CustomerMatch) -> bool:
    """본문에 넣어도 되는 판단: 담당자 [유지], 또는 확인 전이라도 신뢰도 높음."""
    if m.final_matched is not None:
        return m.final_matched
    return m.ai_matched and m.confidence == Confidence.high


def confirmed_ids(item: SelectedItem) -> list[str]:
    return [m.customer_id for m in item.matches if _confirmed(m)]


def _pending(item: SelectedItem) -> list[CustomerMatch]:
    """담당자 확인 전 + 신뢰도 중간 후보. b1 고객사 판단 화면에서 [유지]/[제외]가 필요하다."""
    return [m for m in item.matches if _matched(m) and not _confirmed(m)]


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


def same_maker(item: SelectedItem, customer_id: str | None = None) -> bool:
    """고객사 수입 이력과 제조사가 같은 건 (RULES.md 11-2 순서 1). 강조해서 맨 위에 둔다.

    customer_id를 주면 그 고객사의 판단만 본다 (고객사 메일용).
    """
    return any(
        _confirmed(m)
        and m.rule == MatchRule.maker
        and (customer_id is None or m.customer_id == customer_id)
        for m in item.matches
    )


def _v(x: object) -> str:
    return str(x) if x not in (None, "") else MISSING


def _text() -> dict[str, Any]:
    from app.b2_mail.report.service import config  # service가 이 모듈을 import하므로 늦게 부른다

    data: dict[str, Any] = config()["section1"]
    return data


def _product(item: SelectedItem) -> str:
    """항목 이름 자리: "[식품유형] 제품명".

    제품명이 없는 항목(검사지시 공지, 안내문 등)은 원문 제목을 쓴다.
    제품명도 제목도 없을 때만 "확인 필요".
    """
    e = item.extracted
    title = item.raw.title or MISSING
    if e is None:
        return title
    if e.product_name_ko:
        name = e.product_name_ko + (f"({e.product_name_en})" if e.product_name_en else "")
    else:
        name = e.product_name_en or ""
    food = e.food_type_std or e.food_type_raw
    if not name:
        return f"[{food}] {title}" if food else title  # 공지·안내문: 제목으로 무슨 건인지 보여 준다
    return f"[{_v(food)}] {name}"


def _customers(item: SelectedItem, names: dict[str, str]) -> str:
    """관련 화주: 고객사 이름만 (실제 메일 형식). 판단 근거는 b1 고객사 판단 화면에서 본다.

    같은 제조사로 걸린 고객사에는 강조 표시를 붙인다.
    """
    found = [m for m in item.matches if _confirmed(m)]
    if not found:
        return "없음"
    mark = _text()["same_maker_mark"]
    return ", ".join(
        names.get(m.customer_id, m.customer_id) + (f" {mark}" if m.rule == MatchRule.maker else "")
        for m in found
    )


def _cell(x: object) -> str:
    """표 칸 하나: 줄바꿈·'|'를 지워 표가 깨지지 않게 한다. 빈 칸은 "확인 필요"."""
    return " ".join(_v(x).replace("|", "/").split())


def _own_mark(item: SelectedItem, customer_id: str | None) -> str:
    """고객사 메일: 그 고객사와 같은 제조사로 걸린 건이면 " 【귀사 수입 이력과 같은 제조사】"."""
    if customer_id and same_maker(item, customer_id):
        return " " + _text()["same_maker_mark_customer"]
    return ""


def _unfit_table(
    items: list[SelectedItem],
    names: dict[str, str],
    show_customers: bool,
    customer_id: str | None = None,
) -> list[str]:
    """부적합 표 (실제 메일: 제조국가 | 제조/수출회사 | 식품유형/품목명 | 위반 내역 | 관련 화주).

    RULES.md 12장에 따라 부적합일자·출처 칸을 함께 둔다. 고객사 메일에는 관련 화주 칸이 없고,
    그 고객사와 같은 제조사 건은 제조/수출회사 칸에 표시를 붙인다.
    """
    t = _text()
    head: list[str] = list(t["table_columns"])
    if not show_customers:
        head.remove(t["table_customer_column"])
    rows = [f"   | {' | '.join(head)} |", f"   |{'---|' * len(head)}"]
    for i in items:
        e = i.extracted
        cells = [
            _cell(i.raw.posted_at),
            _cell(e.origin_country if e else None),
            _cell(e.maker if e else None) + _own_mark(i, customer_id),
            _cell(_product(i)),
            _cell(e.violation if e else None),
        ]
        if show_customers:
            cells.append(_cell(_customers(i, names)))
        cells.append(_cell(i.raw.url))
        rows.append(f"   | {' | '.join(cells)} |")
    return rows


def _inspection_block(item: SelectedItem, names: dict[str, str], show_customers: bool) -> list[str]:
    """통관단계 검사지시 한 건 (실제 메일 형식: # 제목 / 가. 나. 다.).

    담당자용: 가. 검사기간 / 나. 관련화주 / 다. 대상 품목 및 검사항목.
    고객사 메일: 관련화주 줄이 없으므로 가. 검사기간 / 나. 대상 품목 및 검사항목.
    """
    t = _text()["inspection_labels"]
    e = item.extracted
    start = _v(e.period_start if e else None)
    end = _v(e.period_end if e else None)
    lines = [f"   # {item.raw.title or MISSING}", f"     {t['period']} : {start} ~ {end}"]
    if show_customers:
        lines.append(f"     {t['customers']} : {_customers(item, names)}")
    target = " / ".join(
        [
            _v(e.origin_country if e else None),
            _v((e.food_type_std or e.food_type_raw) if e else None),
            _v(e.violation if e else None),
        ]
    )
    label = t["targets"] if show_customers else t["targets_customer_mail"]
    lines.append(f"     {label} : {target}")
    lines.append(f"     출처: {_v(item.raw.url)}")
    return lines


def _count_group(title: str, count: int, lines: list[str], empty: str | None) -> list[str]:
    """■ 제목 (N건) + 줄들. N은 항목 수(표 머리줄·여러 줄 묶음과 상관없이)."""
    if not count and empty is None:
        return []
    return [f"  ■ {title} ({count}건)", *(lines if count else [f"     {empty}"])]


def line(
    item: SelectedItem,
    names: dict[str, str],
    show_customers: bool,
    customer_id: str | None = None,
) -> str:
    """항목 한 줄. 부적합: 제조국가 / 제조·수출회사 / [식품유형] 품목명 / 위반 내역."""
    t = _text()
    e = item.extracted
    if show_customers:
        mark = t["same_maker_mark"] + " " if same_maker(item) else ""
    else:
        own = _own_mark(item, customer_id)
        mark = own.lstrip() + " " if own else ""
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


def _pending_line(item: SelectedItem, names: dict[str, str]) -> str:
    cands = " / ".join(
        f"{names.get(m.customer_id, m.customer_id)} ({m.reason})" for m in _pending(item)
    )
    return (
        f"   - [{_v(item.raw.posted_at)}] {_product(item)} / 확인 전 후보: {cands}"
        f"\n     출처: {_v(item.raw.url)}"
    )


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


def _sorted(items: list[SelectedItem], customer_id: str | None = None) -> list[SelectedItem]:
    return sorted(items, key=lambda i: not same_maker(i, customer_id))  # 같은 제조사 건이 먼저


def _split(items: list[SelectedItem]) -> tuple[list[SelectedItem], ...]:
    unfit = [i for i in items if category_of(i) in UNFIT]
    insp = [i for i in items if category_of(i) in INSPECTION]
    other = [i for i in items if i not in unfit and i not in insp]
    return unfit, insp, other


def render(
    items: list[SelectedItem],
    names: dict[str, str],
    empty: str,
    show_customers: bool = True,
    customer_id: str | None = None,
) -> str:
    """본문만 만든다. show_customers=True: 담당자용. False: 고객사 메일(그 고객사 항목만).

    고객사 메일에 customer_id를 주면 그 고객사와 같은 제조사 건에 표시를 붙이고 맨 위에 둔다.
    확인 목록은 check_lines()로 따로 받는다(화면 전용, 메일 글에 넣지 않음).
    """
    t = _text()
    unfit, insp, other = _split(items)

    def blocks(group: list[SelectedItem], show: bool) -> list[str]:
        return [ln for i in group for ln in _inspection_block(i, names, show)]

    if not show_customers:
        if not items:
            return f"  {empty}"
        out: list[str] = []
        table = _unfit_table(_sorted(unfit, customer_id), names, False, customer_id)
        out += _count_group(t["group_unfit"], len(unfit), table, None)
        out += _count_group(t["group_inspection"], len(insp), blocks(insp, False), None)
        others = [line(i, names, False, customer_id) for i in other]
        out += _group(t["group_other"], others, None)
        return "\n".join(out)

    related_unfit = _sorted([i for i in unfit if confirmed_ids(i)])
    related_insp = _sorted([i for i in insp if confirmed_ids(i)])
    # 매주 같은 틀: 본문 묶음은 비어도 남기고 "해당 없음"을 넣는다
    out = [f"  {s}" for s in t["intro"]]
    out.append(f"  {t['source_unfit']}")
    out += _count_group(
        t["group_related"], len(related_unfit), _unfit_table(related_unfit, names, True), empty
    )
    out.append(f"  {t['source_inspection']}")
    out += _count_group(t["group_inspection"], len(related_insp), blocks(related_insp, True), empty)
    return "\n".join(out)


def check_lines(
    items: list[SelectedItem], names: dict[str, str], review: list[SelectedItem]
) -> list[str]:
    """화면 전용 확인 목록: 판단 확인 전, 맞지 않은 부적합·검사지시, 그 밖의 소식, 검토 필요."""
    t = _text()
    unfit, insp, other = _split(items)
    no_unfit = [i for i in unfit if not matched_ids(i)]
    no_insp = [i for i in insp if not matched_ids(i)]
    pending = [i for i in unfit + insp if _pending(i)]
    out: list[str] = []
    out += _group(t["group_unconfirmed"], [_pending_line(i, names) for i in pending], None)
    out += _group(t["group_unmatched_unfit"], [line(i, names, True) for i in no_unfit], None)
    out += _group(t["group_unmatched_inspection"], [line(i, names, True) for i in no_insp], None)
    out += _group(t["group_other"], [line(i, names, True) for i in other], None)
    out += _group(t["group_review"], [_review_line(i) for i in review], None)
    return out
