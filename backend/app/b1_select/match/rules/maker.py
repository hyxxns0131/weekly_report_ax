"""B1-11 규칙 1: 제조사 일치 → high (RULES.md 11-2).

대소문자·공백·쉼표·마침표와 Co./Ltd./Inc. 같은 회사 꼬리를 무시하고 비교한다.
같은 제조사면 근거에 "같은 제조사 → 강조, 별도 안내"를 붙인다(화면에서 굵게).
"""

import re

from app.b1_select.match import reason
from app.b1_select.match.customers import Customer
from app.core.schema import Confidence, CustomerMatch, ExtractedInfo, MatchRule

SUFFIXES = {
    "co",
    "ltd",
    "inc",
    "corp",
    "corporation",
    "limited",
    "llc",
    "company",
    "주식회사",
    "(주)",
}


def normalize_maker(text: str) -> str:
    words = re.sub(r"[.,]", " ", text.lower()).split()
    return "".join(w for w in words if w not in SUFFIXES)


def apply(info: ExtractedInfo, customer: Customer) -> CustomerMatch | None:
    if not info.maker:
        return None
    target = normalize_maker(info.maker)
    if not target:
        return None
    for maker in customer.makers:
        if normalize_maker(maker) == target:
            return CustomerMatch(
                item_id=info.item_id,
                customer_id=customer.customer_id,
                ai_matched=True,
                rule=MatchRule.maker,
                confidence=Confidence.high,
                reason=reason.maker_reason(info.maker, customer.display_name),
            )
    return None
