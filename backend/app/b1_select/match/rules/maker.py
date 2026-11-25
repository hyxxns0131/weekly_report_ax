"""B1-11 규칙 1: 제조사 일치 → high (RULES.md 11-2)."""

from app.b1_select.match import reason
from app.b1_select.match.customers import Customer
from app.core.schema import Confidence, CustomerMatch, ExtractedInfo, MatchRule


def _norm(text: str) -> str:
    return "".join(text.lower().split())


def apply(info: ExtractedInfo, customer: Customer) -> CustomerMatch | None:
    if not info.maker:
        return None
    for maker in customer.makers:
        if _norm(maker) == _norm(info.maker):
            return CustomerMatch(
                item_id=info.item_id,
                customer_id=customer.customer_id,
                ai_matched=True,
                rule=MatchRule.maker,
                confidence=Confidence.high,
                reason=reason.maker_reason(info.maker, customer.display_name),
            )
    return None
