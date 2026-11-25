"""섹션 3 오늘의 팁 (B2-07, P2). 근거 없는 팁은 넣지 않는다."""


def render(tip: str | None, empty: str) -> str:
    return f"   - {tip}" if tip else f"   {empty}"
