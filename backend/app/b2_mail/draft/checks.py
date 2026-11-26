"""초안 경고 (AGENTS.md 7-6, RULES.md 11-5): 출처 누락 · 다른 고객사명 · 원문에 없는 숫자."""

import re

from app.core.schema import WeeklySelection

NUM = re.compile(r"\d+(?:[.,]\d+)?")
# 링크 안 숫자는 주소 일부라 검출값·날짜·고시번호가 아니다 (7-6 검사 대상 아님).
URL = re.compile(r"https?://\S+")

MISSING_SOURCE = "출처 누락"
OTHER_CUSTOMER = "다른 고객사명 포함"
UNKNOWN_NUMBER = "원문에 없는 숫자"
NOT_CHECKED = "고친 본문을 검사하지 못했습니다"
# 본문 검사에서 나온 경고. 본문이 바뀌면 이것만 지우고 다시 검사한다 (다른 경고는 그대로).
BODY_CHECK_PREFIXES = (MISSING_SOURCE, OTHER_CUSTOMER, UNKNOWN_NUMBER, NOT_CHECKED)


def corpus(ws: WeeklySelection) -> str:
    parts = [ws.week_label, str(ws.period_start), str(ws.period_end)]
    for i in ws.items:
        parts += [i.raw.title, i.raw.body, str(i.raw.posted_at or ""), i.raw.url or ""]
        if i.extracted:
            parts += [str(v) for v in i.extracted.model_dump().values() if v]
    for c in ws.law_changes:
        parts += [str(v) for v in c.model_dump().values() if v]
    return "\n".join(parts)


def check(body: str, ws: WeeklySelection, other_customer_names: list[str]) -> list[str]:
    warnings: list[str] = []
    missing = body.count("출처: 확인 필요")
    if missing:
        warnings.append(f"{MISSING_SOURCE} {missing}건")
    for name in other_customer_names:
        if name and name in body:
            warnings.append(f"{OTHER_CUSTOMER}: {name}")
    src = corpus(ws)
    unknown = sorted({n for n in NUM.findall(URL.sub(" ", body)) if len(n) >= 2 and n not in src})
    if unknown:
        warnings.append(f"{UNKNOWN_NUMBER}: " + ", ".join(unknown[:5]))
    return warnings


def other_warnings(warnings: list[str]) -> list[str]:
    """본문 검사 경고를 뺀 나머지(고객사 판단 후보·대상 제외 등)."""
    return [w for w in warnings if not w.startswith(BODY_CHECK_PREFIXES)]


def not_checked(reason: str) -> str:
    return f"{NOT_CHECKED} ({reason}). 다시 저장하거나 초안을 다시 만들어 주세요"
