"""B1-11 규칙 4: 원산지 일치 + 상위 식품유형만 일치 → medium(검토 필요)."""

from app.b1_select.food_type.country import normalize_country
from app.b1_select.food_type.hierarchy import parent_of
from app.b1_select.food_type.normalize import normalize_food_type
from app.b1_select.match import reason
from app.b1_select.match.customers import Customer
from app.core.schema import Confidence, CustomerMatch, ExtractedInfo, MatchRule


def apply(info: ExtractedInfo, customer: Customer) -> CustomerMatch | None:
    food = normalize_food_type(info.food_type_std or info.food_type_raw)
    country = normalize_country(info.origin_country)
    parent = parent_of(food)
    if not (parent and country):
        return None
    for k in customer.keywords:
        if k.origin_country == country and parent_of(k.food_type) == parent:
            return CustomerMatch(
                item_id=info.item_id,
                customer_id=customer.customer_id,
                ai_matched=True,
                rule=MatchRule.food_type_parent,
                confidence=Confidence.medium,
                reason=reason.parent_reason(country, parent, customer.display_name),
            )
    return None
