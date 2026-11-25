"""B1-14 법령 API ↔ 식약처 주간 공문 대조 (P1).

공문 수집(B1-05·07)이 준비되면 법령명·번호로 맞춰 match / api_only / notice_only를 단다.
지금은 공문이 없으므로 모두 not_checked로 둔다.
"""

from app.core.schema import Crosscheck, LawChange


def crosscheck(api_changes: list[LawChange], notices: list[LawChange]) -> list[LawChange]:
    if not notices:
        for c in api_changes:
            c.crosscheck = Crosscheck.not_checked
            c.crosscheck_note = "공문 수집 전"
        return api_changes
    keys = {(n.law_name, n.number) for n in notices}
    for c in api_changes:
        c.crosscheck = Crosscheck.match if (c.law_name, c.number) in keys else Crosscheck.api_only
    return api_changes
