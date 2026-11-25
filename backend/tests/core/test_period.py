from datetime import date

import pytest

from app.core.period import report_period, week_of_month


@pytest.mark.parametrize(
    ("reference", "start", "end"),
    [
        (date(2026, 11, 25), date(2026, 11, 16), date(2026, 11, 22)),  # 수요일 → 지난주
        (date(2026, 11, 23), date(2026, 11, 16), date(2026, 11, 22)),  # 월요일 → 지난주
        (date(2026, 11, 27), date(2026, 11, 23), date(2026, 11, 29)),  # 금요일 → 이번 주
        (date(2026, 11, 29), date(2026, 11, 23), date(2026, 11, 29)),  # 일요일 → 이번 주
    ],
)
def test_report_period(reference: date, start: date, end: date) -> None:
    p = report_period(reference)
    assert (p.period_start, p.period_end) == (start, end)


def test_week_label_matches_design_example() -> None:
    # DESIGN.md 3장: 2026년 11월 3주차 (11/16 월 ~ 11/22 일)
    assert report_period(date(2026, 11, 25)).week_label == "2026년 11월 3주차"


def test_week_of_month_first_week_contains_day_one() -> None:
    assert week_of_month(date(2026, 11, 1)) == 1
    assert week_of_month(date(2026, 11, 2)) == 1  # 1일(일)과 같은 주
    assert week_of_month(date(2026, 11, 8)) == 2
