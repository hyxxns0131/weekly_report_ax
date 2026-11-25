"""B2-02 담당자용 주간 요약 메일 초안 (DESIGN.md 10-1)."""

from app.b2_mail.report.service import ReportOut, config


def _mmdd(d: object) -> str:
    s = str(d)
    return f"{s[5:7]}/{s[8:10]}"


def subject(out: ReportOut, template: str) -> str:
    r = out.report
    return template.format(
        week_label=r.week_label, period=f"{_mmdd(r.period_start)}~{_mmdd(r.period_end)}"
    )


def body(out: ReportOut, crosscheck_issues: int) -> str:
    return (
        "안녕하세요. 이번 주 수입식품 검역 관련 소식을 정리해 드립니다.\n\n"
        f"{out.text}\n\n"
        f"(담당자 확인용) 검토 필요 {out.review_needed}건 · "
        f"법령 대조 불일치 {crosscheck_issues}건\n\n"
        "감사합니다."
    )


_ = config  # 섹션 문구는 config/b2/report.json
