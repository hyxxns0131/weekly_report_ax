"""B1-08 키워드 1차 필터 (RULES.md 11-1). 키워드는 힌트일 뿐, 애매하면 검토 필요."""

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


def classify(title: str, body: str) -> tuple[Label, Category, str, str]:
    """(라벨, 구분, 사유, 근거 인용)."""
    text = f"{title}\n{body}"
    s = _scope()
    category = Category.other
    if "부적합" in text:
        category = Category.unfit
    elif "검사지시" in text or "정밀검사" in text:
        category = Category.inspection_order
    elif first_hit(text, s["law_keywords"]):
        category = Category.law_change

    ex = first_hit(text, s["exclude"])
    inc = first_hit(text, s["include"])
    if ex and not inc:
        return Label.irrelevant, category, f"제외 키워드 '{ex}' 포함", ex
    if inc and not ex:
        return Label.relevant, category, f"수입식품 키워드 '{inc}' 포함", inc
    reason = "대상 판단이 애매함(포함·제외 키워드가 함께 있거나 없음)"
    return Label.review_needed, category, reason, inc or ex or ""
