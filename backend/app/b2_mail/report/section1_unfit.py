"""섹션 1 부적합·통관단계 검사지시 (DESIGN.md 10-1). 숫자·날짜는 입력 값만 쓴다."""

from app.core.schema import Category, Label, SelectedItem

UNFIT = {Category.unfit}
INSPECTION = {Category.inspection_order}


def label_of(item: SelectedItem) -> Label:
    return item.selection.final_label or item.selection.ai_label


def category_of(item: SelectedItem) -> Category:
    return item.selection.final_category or item.selection.ai_category


def matched_ids(item: SelectedItem) -> list[str]:
    return [
        m.customer_id
        for m in item.matches
        if (m.final_matched if m.final_matched is not None else m.ai_matched)
    ]


def pick(items: list[SelectedItem]) -> list[SelectedItem]:
    """보고서 섹션 1: 선별이 '관련'인 부적합·검사지시·기타 관련 소식."""
    return [
        i for i in items if label_of(i) == Label.relevant and category_of(i) != Category.law_change
    ]


def _v(x: object) -> str:
    return str(x) if x not in (None, "") else "확인 필요"


def line(item: SelectedItem, names: dict[str, str], show_customers: bool) -> str:
    e = item.extracted
    head = f"   - [{_v(item.raw.posted_at)}] "
    if e and category_of(item) in UNFIT:
        name = _v(e.product_name_ko) + (f"({e.product_name_en})" if e.product_name_en else "")
        food = _v(e.food_type_std or e.food_type_raw)
        head += f"{name} / {food} / {_v(e.origin_country)} / {_v(e.maker)}"
        body = f"\n     위반 내역: {_v(e.violation)}"
    elif e and category_of(item) in INSPECTION:
        head += (
            f"통관단계 검사지시: {_v(e.origin_country)} / {_v(e.food_type_std or e.food_type_raw)}"
            f" / 기간 {_v(e.period_start)}~{_v(e.period_end)}"
        )
        body = f"\n     검사 항목: {_v(e.violation)}"
    else:
        head += item.raw.title
        body = ""
    cust = ""
    if show_customers:
        ids = matched_ids(item)
        cust = "\n     관련 고객사: " + (", ".join(names.get(i, i) for i in ids) if ids else "없음")
    src = f"\n     출처: {item.raw.url or '확인 필요'}"
    return head + body + cust + src


def render(
    items: list[SelectedItem], names: dict[str, str], empty: str, show_customers: bool = True
) -> str:
    if not items:
        return f"  {empty}"
    unfit = [i for i in items if category_of(i) in UNFIT]
    insp = [i for i in items if category_of(i) in INSPECTION]
    other = [i for i in items if i not in unfit and i not in insp]
    parts: list[str] = []
    for title, group in (
        ("부적합", unfit),
        ("통관단계 검사지시", insp),
        ("그 밖의 관련 소식", other),
    ):
        if group:
            parts.append(f"  ■ {title} ({len(group)}건)")
            parts.extend(line(i, names, show_customers) for i in group)
    return "\n".join(parts)
