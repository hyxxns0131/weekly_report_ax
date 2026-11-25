"""보고 기간·주차 계산 (C-01). 현황(KHS)·법령(LSH)·보고서(KHW)가 함께 쓴다.

규칙 (RULES.md 11-4, 기존 도구 build_weekly 이어받음, SAMC 확인 필요):
- 금·토·일에 실행하면 이번 주(월~일), 월~목에 실행하면 지난주(월~일).
- 주차: 보고 기간 월요일이 속한 달에서 1일이 들어 있는 주를 1주차로 센다.
  주는 일요일에 시작하는 달력 기준으로 센다. DESIGN.md 3장 예시
  "2026년 11월 3주차 (11/16 월 ~ 11/22 일)"와 맞추기 위한 선택이며 SAMC 확인 필요.
"""

from datetime import date, timedelta

from pydantic import BaseModel

FRIDAY = 4


class ReportPeriod(BaseModel):
    period_start: date
    period_end: date
    week_label: str


def week_of_month(day: date) -> int:
    """일요일 시작 달력에서 `day`가 그 달 몇째 주인지 (1일이 든 주 = 1주차)."""
    first = day.replace(day=1)
    offset = (first.weekday() + 1) % 7  # 1일 앞에 있는 같은 주의 날 수 (일요일 = 0)
    return (day.day + offset - 1) // 7 + 1


def report_period(reference: date) -> ReportPeriod:
    monday_this_week = reference - timedelta(days=reference.weekday())
    start = (
        monday_this_week if reference.weekday() >= FRIDAY else monday_this_week - timedelta(days=7)
    )
    end = start + timedelta(days=6)
    label = f"{start.year}년 {start.month}월 {week_of_month(start)}주차"
    return ReportPeriod(period_start=start, period_end=end, week_label=label)
