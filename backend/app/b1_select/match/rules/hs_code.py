"""B1-11 규칙 2: HS 코드 일치 → high. 공개 부적합 목록에는 HS 칸이 없어 대부분 건너뛴다."""

from app.b1_select.match import reason
from app.b1_select.match.customers import Customer
from app.core.schema import Confidence, CustomerMatch, ExtractedInfo, MatchRule


def apply(info: ExtractedInfo, customer: Customer) -> CustomerMatch | None:
    if not info.hs_code:
        return None
    for hs in customer.hs_codes:
        if info.hs_code.startswith(hs) or hs.startswith(info.hs_code):
            return CustomerMatch(
                item_id=info.item_id,
                customer_id=customer.customer_id,
                ai_matched=True,
                rule=MatchRule.hs_code,
                confidence=Confidence.high,
                reason=reason.hs_reason(info.hs_code, customer.display_name),
            )
    return None
