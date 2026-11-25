"""B1-11 규칙 5: 식품유형만 일치 → medium(검토 필요)."""

from app.b1_select.food_type.normalize import normalize_food_type
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
