"""B2-02 담당자용 주간 요약 메일 초안 (DESIGN.md 10-1, 실제 예시 11월 4주차 메일).

- 본문 = 머리말(수신자·인사·보내는 사람·도입) + 보고서 섹션 1~3 + 맺음말.
- 문구는 config/b2/mail.json의 staff_body에서만 고친다.
- 검토 필요·법령 대조 불일치 건수는 메일로 나가면 안 되므로 본문에 넣지 않고
  warnings()로 초안 경고에만 담는다.
"""

from typing import Any

from app.b2_mail.report.service import ReportOut


def _mmdd(d: object) -> str:
    s = str(d)
    return f"{s[5:7]}/{s[8:10]}"


def subject(out: ReportOut, template: str) -> str:
    r = out.report
    return template.format(
        week_label=r.week_label, period=f"{_mmdd(r.period_start)}~{_mmdd(r.period_end)}"
    )


def body(out: ReportOut, cfg: dict[str, Any]) -> str:
    t = cfg["staff_body"]
    head = "\n".join([t["greeting"], t["sender"]])
    intro = t["intro"].format(week_label=out.report.week_label)
    return "\n\n".join([t["recipient"], head, intro, out.text, t["closing"]])


def warnings(out: ReportOut, crosscheck_issues: int, cfg: dict[str, Any]) -> list[str]:
    t = cfg["staff_warnings"]
    found: list[str] = []
    if out.review_needed:
        found.append(t["review_needed"].format(count=out.review_needed))
    if crosscheck_issues:
        found.append(t["crosscheck_mismatch"].format(count=crosscheck_issues))
    return found
