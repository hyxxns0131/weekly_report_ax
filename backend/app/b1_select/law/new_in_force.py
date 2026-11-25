"""B1-12 보고 기간에 "새로 시행된" 개정 고르기 (RULES.md 11-3, 기존 도구 규칙).

- 시행일이 (보고 기간 월요일 - 14일) ~ 보고 기간 일요일 사이인 것만. 시행 예정은 넣지 않는다.
- 이미 보고한 개정(reported.py)은 뺀다.
"""

from datetime import date, timedelta

from app.core.schema import LawChange

LOOKBACK_DAYS = 14


def window(period_start: date, period_end: date) -> tuple[date, date]:
    return period_start - timedelta(days=LOOKBACK_DAYS), period_end


def pick(
    changes: list[LawChange], period_start: date, period_end: date, reported: set[str]
) -> list[LawChange]:
    lo, hi = window(period_start, period_end)
    return [
        c for c in changes if c.effective_at and lo <= c.effective_at <= hi and c.id not in reported
    ]
