"""B1-11 규칙 3: 원산지 + 식품유형이 키워드와 일치 → high."""

from app.b1_select.food_type.country import normalize_country
from app.b1_select.food_type.normalize import normalize_food_type
from app.b1_select.match import reason
from app.b1_select.match.customers import Customer
from app.core.schema import Confidence, CustomerMatch, ExtractedInfo, MatchRule


def apply(info: ExtractedInfo, customer: Customer) -> CustomerMatch | None:
    food = normalize_food_type(info.food_type_std or info.food_type_raw)
    country = normalize_country(info.origin_country)
    if not food:
        return None
    keywords = ", ".join(k.food_type for k in customer.keywords)
    for k in customer.keywords:
        if k.food_type == food and (k.origin_country is None or k.origin_country == country):
            return CustomerMatch(
                item_id=info.item_id,
                customer_id=customer.customer_id,
                ai_matched=True,
                rule=MatchRule.origin_food_type,
                confidence=Confidence.high,
                reason=reason.origin_food_type_reason(
                    country or "전 국가", food, customer.display_name, keywords
                ),
            )
    return None
