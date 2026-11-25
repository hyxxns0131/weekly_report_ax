"""알림 — 이번 주 바뀐 점 (C-06, DESIGN.md 3-2).

법령 개정(law_change_work)과 통관단계 검사지시(selection·extracted_info·customer_match)를
로컬 DB에서 읽어 만든다. b1 코드를 import하지 않는다. 숫자·날짜는 저장된 원문 값만 쓴다.
"""

import json
from typing import Literal

from pydantic import BaseModel

from app.core.storage import local_db

NoticeKind = Literal["law_change", "inspection_order"]
NoticeAction = Literal["read", "dismiss"]


class Notice(BaseModel):
    id: str  # 법령: LawChange.id, 검사지시: inspection:{item_id}
    kind: NoticeKind
    title: str
    summary: str | None  # 한 줄 요지 (없으면 화면에서 "확인 필요")
    summary_is_ai: bool  # final_summary가 없어 AI 요지를 쓰는 경우
    crosscheck: str | None  # 법령만: match, api_only, notice_only, not_checked
    effective_at: str | None
    food_types: list[str]
    customers: list[str]  # 가명 ID (C001 등)
    source: str | None
    url: str | None
    read_by: str | None
    read_at: str | None


class NoticeList(BaseModel):
    items: list[Notice]  # 지운 것은 빠진다
    unread: int
    total: int  # 지운 것까지 포함한 이번 주 소식 수 (0이면 "해당 없음")


def _food_types(raw: object) -> list[str]:
    if not raw:
        return []
    try:
        val = json.loads(str(raw))
    except json.JSONDecodeError:
        return [str(raw)]
    return [str(v) for v in val] if isinstance(val, list) else [str(val)]


def _law_notices(run_id: int) -> list[Notice]:
    out: list[Notice] = []
    for r in local_db.notice_laws(run_id):
        final = r.get("final_summary")
        ai = r.get("ai_summary")
        name = str(r.get("law_name") or "법령명 확인 필요")
        change = r.get("change_type")
        out.append(
            Notice(
                id=str(r["id"]),
                kind="law_change",
                title=f"「{name}」 {change}" if change else f"「{name}」",
                summary=str(final) if final else (str(ai) if ai else None),
                summary_is_ai=not final and bool(ai),
                crosscheck=str(r.get("crosscheck") or "not_checked"),
                effective_at=str(r["effective_at"]) if r.get("effective_at") else None,
                food_types=_food_types(r.get("related_food_types")),
                customers=[],
                source="법령 개정",
                url=str(r["source_url"]) if r.get("source_url") else None,
                read_by=None,
                read_at=None,
            )
        )
    return out


def _inspection_notices(run_id: int) -> list[Notice]:
    out: list[Notice] = []
    for r in local_db.notice_inspections(run_id):
        food = r.get("food_type_std") or r.get("food_type_raw") or r.get("product_name_ko")
        country = r.get("origin_country")
        head = " · ".join(str(v) for v in (country, food) if v)
        period = ""
        if r.get("period_start") or r.get("period_end"):
            period = f" ({r.get('period_start') or '?'} ~ {r.get('period_end') or '?'})"
        violation = r.get("violation")
        customers = str(r.get("customers") or "")
        out.append(
            Notice(
                id=f"inspection:{r['item_id']}",
                kind="inspection_order",
                title=head or str(r.get("title") or "제목 확인 필요"),
                summary=f"{violation}{period}" if violation else (period.strip() or None),
                summary_is_ai=False,
                crosscheck=None,
                effective_at=None,
                food_types=[str(food)] if food else [],
                customers=[c for c in customers.split(",") if c],
                source=str(r.get("source") or "") or None,
                url=str(r["url"]) if r.get("url") else None,
                read_by=None,
                read_at=None,
            )
        )
    return out


def list_notices(run_id: int) -> NoticeList:
    all_items = _law_notices(run_id) + _inspection_notices(run_id)
    states = local_db.notice_states([n.id for n in all_items])
    items: list[Notice] = []
    for n in all_items:
        st = states.get(n.id)
        if st and st.dismissed_at:
            continue
        if st:
            n.read_by, n.read_at = st.read_by, st.read_at
        items.append(n)
    return NoticeList(
        items=items,
        unread=sum(1 for n in items if n.read_at is None),
        total=len(all_items),
    )


def mark(
    notice_id: str, run_id: int | None, action: NoticeAction, user: str
) -> local_db.NoticeState:
    return local_db.mark_notice(notice_id, run_id, action, user)
