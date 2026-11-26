"""B1-11 규칙 5: 식품유형만 일치 → medium(검토 필요).

법령·정책 항목은 원산지·식품유형 칸이 없으므로
본문에 나온 식품유형 단어로 같은 규칙을 쓴다(apply_text).
"""

from app.b1_select.food_type.normalize import find_food_types, normalize_food_type
from app.b1_select.match import reason
from app.b1_select.match.customers import Customer
from app.core.schema import Confidence, CustomerMatch, ExtractedInfo, MatchRule


def apply(info: ExtractedInfo, customer: Customer) -> CustomerMatch | None:
    food = normalize_food_type(info.food_type_std or info.food_type_raw)
    if not food:
        return None
    if any(k.food_type == food for k in customer.keywords):
        return CustomerMatch(
            item_id=info.item_id,
            customer_id=customer.customer_id,
            ai_matched=True,
            rule=MatchRule.food_type_only,
            confidence=Confidence.medium,
            reason=reason.food_type_only_reason(food, customer.display_name),
        )
    return None


def apply_text(item_id: str, text: str, customer: Customer) -> CustomerMatch | None:
    wanted = {k.food_type for k in customer.keywords}
    word = next((f for f in find_food_types(text) if f in wanted), None)
    if word is None:
        return None
    return CustomerMatch(
        item_id=item_id,
        customer_id=customer.customer_id,
        ai_matched=True,
        rule=MatchRule.food_type_only,
        confidence=Confidence.medium,
        reason=reason.body_food_type_reason(word, customer.display_name),
    )
