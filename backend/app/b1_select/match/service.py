"""B1-11 관련 고객사 판단. 규칙 순서대로 보고 처음 맞는 규칙 하나를 쓴다 (RULES.md 11-2).

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
from app.core.schema import CustomerMatch, ExtractedInfo
from app.core.storage import repo

Rule = Callable[[ExtractedInfo, Customer], CustomerMatch | None]
RULES: list[Rule] = [
    maker.apply,
    hs_code.apply,
    origin_food_type.apply,
    food_type_parent.apply,
    food_type_only.apply,
]


def judge(info: ExtractedInfo, customers: list[Customer]) -> list[CustomerMatch]:
    out: list[CustomerMatch] = []
    for c in customers:
        for rule in RULES:
            m = rule(info, c)
            if m:
                out.append(m)
                break
    return out


def match_item(item_id: str, customers: list[Customer] | None = None) -> None:
    repo.delete_ai_matches(item_id)
    info = repo.get_extracted(item_id)
    if info is None:
        return
    kept = {m.customer_id for m in repo.list_matches_for_item(item_id)}
    for m in judge(info, customers or load_customers()):
        if m.customer_id not in kept:
            repo.save_match(m)


def clear_item(item_id: str) -> None:
    repo.delete_ai_matches(item_id)
