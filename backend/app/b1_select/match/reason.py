"""B1-11 근거 문장 만들기 (RULES.md 11-2, 기존 도구 import_failures.related 형식)."""


def maker_reason(maker: str, customer: str) -> str:
    return f"같은 제조사 수입 이력: {maker} ({customer})"


def hs_reason(hs: str, customer: str) -> str:
    return f"HS 코드 {hs} 일치 ({customer}) · HS 기준 연도 확인 필요"


def origin_food_type_reason(country: str, food_type: str, customer: str, keywords: str) -> str:
    return f"원산지 '{country}' + 식품유형 '{food_type}' 일치 ({customer} 키워드: {keywords})"


def parent_reason(country: str, parent: str, customer: str) -> str:
    return (
        f"원산지 '{country}' 일치, 식품유형은 상위 분류 '{parent}'만 일치 ({customer}) · 검토 필요"
    )


def food_type_only_reason(food_type: str, customer: str) -> str:
    return f"식품유형 '{food_type}'만 일치(원산지 다름) ({customer}) · 검토 필요"
