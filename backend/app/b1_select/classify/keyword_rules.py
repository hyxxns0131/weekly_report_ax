"""B1-08 선별: 순서형 규칙 Q1~Q4 (RULES.md 11-1). 점수제가 아니다.

위에서부터 보고, 처음 "예"가 나온 질문에서 정한다. 단어 목록은 config/b1/scope.json에만 둔다.
- Q1 목록 출처(부적합·검사지시) → 관련.
       단, 제외 단어가 있고 식품 단어가 없으면 검토 필요.
- Q2 제외 단어 → 무관.
       바로 뒤에 성분·함유 등이 오면 제외하지 않는다("의약품 성분 함유 젤리").
       식품 단어가 같이 있으면 검토 필요.
       국내식품·접객업소는 '수입' 말이 있으면 검토 필요.
- Q3 강한 단어(수입식품·검사지시 등) → 관련. 약한 단어(수입·통관)는 식품 단어와 같이 있을 때만.
- Q4 나머지 → 검토 필요 (누락 방지).
ai_reason은 화면 ? 안에 그대로 보이므로 짧게 쓴다.
"""

import json
from functools import lru_cache
from typing import Any

from app.core.config import REPO_ROOT
from app.core.schema import Category, Label

SCOPE = REPO_ROOT / "backend" / "config" / "b1" / "scope.json"


@lru_cache
def _scope() -> dict[str, Any]:
    data: dict[str, Any] = json.loads(SCOPE.read_text(encoding="utf-8"))
    return data


def first_hit(text: str, words: list[str]) -> str | None:
    return next((w for w in words if w in text), None)


def _excluded_hit(text: str, words: list[str], after: list[str]) -> str | None:
    """제외 단어 중 뒤에 '성분·함유…'가 붙지 않은 것이 하나라도 있으면 그 단어."""
    for w in words:
        start = text.find(w)
        while start != -1:
            rest = text[start + len(w) :].lstrip()
            if not any(rest.startswith(a) for a in after):
                return w
            start = text.find(w, start + 1)
    return None


def category_of(text: str, source: str | None) -> Category:
    s = _scope()
    by_source: dict[str, str] = s.get("source_category", {})
    if source in by_source:
        return Category(by_source[source])
    if first_hit(text, s["unfit_words"]):
        return Category.unfit
    if first_hit(text, s["inspection_words"]):
        return Category.inspection_order
    if first_hit(text, s["law_words"]):
        return Category.law_change
    if first_hit(text, s["policy_words"]):
        return Category.policy_news
    return Category.other


def classify(title: str, body: str, source: str | None = None) -> tuple[Label, Category, str, str]:
    """(라벨, 구분, 사유, 근거 단어)."""
    text = f"{title}\n{body}"
    s = _scope()
    category = category_of(text, source)
    after: list[str] = s["ingredient_after"]
    food = first_hit(text, s["food_words"])
    ex = _excluded_hit(text, s["exclude"], after)
    domestic = _excluded_hit(text, s["exclude_domestic"], after)

    # Q1 목록 출처
    if source in s["list_sources"]:
        if (ex or domestic) and not food:
            word = ex or domestic or ""
            return Label.review_needed, category, f"Q1 목록 출처지만 '{word}' 포함", word
        return Label.relevant, category, "Q1 수입식품 목록 출처", source or ""

    # Q2 제외 대상
    if ex:
        if food:
            return Label.review_needed, category, f"Q2 '{ex}' + 식품 단어 '{food}'", ex
        return Label.irrelevant, category, f"Q2 제외 대상: {ex}", ex
    if domestic:
        if "수입" in text:
            return Label.review_needed, category, f"Q2 '{domestic}' + '수입' 같이 있음", domestic
        return Label.irrelevant, category, f"Q2 제외 대상: {domestic}", domestic

    # Q3 수입식품 단어
    strong = first_hit(text, s["strong"])
    if strong:
        return Label.relevant, category, f"Q3 수입식품 단어: {strong}", strong
    weak = first_hit(text, s["weak"])
    if weak and food:
        return Label.relevant, category, f"Q3 '{weak}' + 식품 단어 '{food}'", f"{weak}, {food}"

    # Q4 나머지
    return Label.review_needed, category, "Q4 판단 근거 부족", weak or ""
