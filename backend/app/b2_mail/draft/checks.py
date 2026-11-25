"""초안 경고 (AGENTS.md 7-6, RULES.md 11-5): 출처 누락 · 다른 고객사명 · 원문에 없는 숫자."""

import re

from app.core.schema import WeeklySelection

NUM = re.compile(r"\d+(?:[.,]\d+)?")


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
        warnings.append(f"출처 누락 {missing}건")
    for name in other_customer_names:
        if name and name in body:
            warnings.append(f"다른 고객사명 포함: {name}")
    src = corpus(ws)
    unknown = sorted({n for n in NUM.findall(body) if len(n) >= 2 and n not in src})
    if unknown:
        warnings.append("원문에 없는 숫자: " + ", ".join(unknown[:5]))
    return warnings
