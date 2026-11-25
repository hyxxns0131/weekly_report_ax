"""섹션 2 법령 개정 요약 (DESIGN.md 10-1). 없으면 "해당 없음" 문장."""

from app.core.schema import LawChange


def _v(x: object) -> str:
    return str(x) if x not in (None, "") else "확인 필요"


def render(changes: list[LawChange], empty: str) -> str:
    if not changes:
        return f"   {empty}"
    lines = []
    for c in changes:
        summary = c.final_summary or c.ai_summary
        lines.append(
            f"   - 「{_v(c.law_name)}」 {_v(c.change_type)}({_v(c.number)})"
            f" · 시행 {_v(c.effective_at)}\n"
            f"     주요 내용: {_v(summary)}\n"
            f"     관련 식품유형: {', '.join(c.related_food_types) or '확인 필요'}"
            f" / 출처: {_v(c.source_url)}"
        )
    return "\n".join(lines)
