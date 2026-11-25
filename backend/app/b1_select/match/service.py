"""B1-11 관련 고객사 판단. 규칙 순서대로 보고 처음 맞는 규칙 하나를 쓴다 (RULES.md 11-2).

순서: maker → hs_code → origin_food_type → food_type_parent → food_type_only.
- HS 코드는 원문에 있을 때만 본다(추정하지 않는다).
- 원산지나 식품유형이 비어 있으면 식품유형 규칙(3~5)은 건너뛴다. 항목 선별은 바꾸지 않는다.
- 법령·정책 항목(law_change, policy_news)은 본문의 식품유형 단어로 food_type_only(medium)를 단다.
재실행 때 담당자가 정한 final_matched는 덮어쓰지 않는다 (AGENTS.md 0-5).
"""

from collections.abc import Callable

from app.b1_select.match.customers import Customer, load_customers
from app.b1_select.match.rules import (
    food_type_only,
    food_type_parent,
    hs_code,
    maker,
    origin_food_type,
)
from app.core.schema import Category, CustomerMatch, ExtractedInfo
from app.core.storage import repo

Rule = Callable[[ExtractedInfo, Customer], CustomerMatch | None]
ID_RULES: list[Rule] = [maker.apply, hs_code.apply]
FOOD_RULES: list[Rule] = [origin_food_type.apply, food_type_parent.apply, food_type_only.apply]
RULES: list[Rule] = ID_RULES + FOOD_RULES
TEXT_CATEGORIES = {Category.law_change, Category.policy_news}


def judge(
    info: ExtractedInfo,
    customers: list[Customer],
    category: Category | None = None,
    text: str = "",
) -> list[CustomerMatch]:
    by_text = category in TEXT_CATEGORIES
    has_food = bool(info.origin_country and (info.food_type_std or info.food_type_raw))
    rules = RULES if has_food else ID_RULES
    out: list[CustomerMatch] = []
    for c in customers:
        m = None
        for rule in rules:
            m = rule(info, c)
            if m:
                break
        if m is None and by_text:
            m = food_type_only.apply_text(info.item_id, text, c)
        if m:
            out.append(m)
    return out


def match_item(item_id: str, customers: list[Customer] | None = None) -> None:
    repo.delete_ai_matches(item_id)
    info = repo.get_extracted(item_id)
    if info is None:
        return
    sel = repo.get_selection(item_id)
    category = (sel.final_category or sel.ai_category) if sel else None
    raw = repo.get_raw(item_id)
    text = f"{raw.title}\n{raw.body}" if raw else ""
    kept = {m.customer_id for m in repo.list_matches_for_item(item_id)}
    for m in judge(info, customers or load_customers(), category, text):
        if m.customer_id not in kept:
            repo.save_match(m)


def clear_item(item_id: str) -> None:
    repo.delete_ai_matches(item_id)
