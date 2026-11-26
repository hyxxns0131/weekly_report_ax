"""B2-01 주간 보고서 조립. 섹션 1~3 고정 틀, 내용이 없으면 "해당 없음" (RULES.md 11-5).

- 각 섹션 파일은 본문(render)과 담당자 확인 목록(check_lines)을 따로 돌려준다.
- text = 메일로 나가는 본문(섹션 1~3)만. 확인 목록은 text에 넣지 않고 check 칸에 따로 담는다.
  check는 보고서 화면(ReportPreview)에만 보이고 메일 초안에는 들어가지 않는다.
  확인·확정은 b1 화면(수집·선별, 고객사 판단)에서 하고 보고서를 다시 조립한다.
- 문구·섹션 이름은 config/b2/report.json에만 둔다 (Jinja2 템플릿은 쓰지 않음, 4단계 결정).
"""

import json
from datetime import date
from typing import Any

from pydantic import BaseModel

from app.b2_mail.input import load_customer_names, load_selection
from app.b2_mail.report import section1_unfit, section2_law, section3_tip
from app.core.config import REPO_ROOT
from app.core.schema import Category, Label, SelectedItem, WeeklyReport, WeeklySelection
from app.core.storage import repo

REPORT_JSON = REPO_ROOT / "backend" / "config" / "b2" / "report.json"


class ReportOut(BaseModel):
    report: WeeklyReport
    text: str  # 메일로 나가는 본문만
    review_needed: int
    customer_names: dict[str, str]
    check: str = ""  # 화면 전용 확인 목록 (메일 초안에 넣지 않는다)


def config() -> dict[str, Any]:
    data: dict[str, Any] = json.loads(REPORT_JSON.read_text(encoding="utf-8"))
    return data


def _mmdd(d: date) -> str:
    return f"{d.month:02d}/{d.day:02d}"


def _check_text(cfg: dict[str, Any], checks: list[list[str]]) -> str:
    """섹션별 확인 목록을 [1. …] [2. …] [3. …]로 묶은 화면용 글. 없으면 빈 글."""
    parts = [
        "\n".join([f" [{label}]", *lines])
        for label, lines in zip(cfg["check_section_labels"], checks, strict=True)
        if lines
    ]
    return "\n".join(parts)


def _board_law(ws: WeeklySelection) -> list[SelectedItem]:
    """선별 목록에서 '법령 개정'으로 분류된 관련·검토 필요 글 (섹션 1에서는 빠지는 글)."""
    return [
        i
        for i in ws.items
        if section1_unfit.category_of(i) == Category.law_change
        and section1_unfit.label_of(i) in (Label.relevant, Label.review_needed)
    ]


def build(run_id: int, token: str | None, source: str = "api") -> tuple[ReportOut, WeeklySelection]:
    ws = load_selection(run_id, token, source)
    names = load_customer_names(token, source)
    saved = repo.get_report(run_id) or {}
    tip = saved.get("tip")
    reannounce = saved.get("reannounce")
    cfg = config()
    report = WeeklyReport(
        run_id=run_id,
        period_start=ws.period_start,
        period_end=ws.period_end,
        week_label=ws.week_label,
        section1_items=section1_unfit.pick(ws.items),
        section2_items=ws.law_changes,
        section3_tip=tip,
    )
    review = sum(1 for i in ws.items if section1_unfit.label_of(i) == Label.review_needed)
    t = cfg["section_titles"]
    period = (ws.period_start, ws.period_end)
    title1 = t[0] + cfg["section1_period"].format(
        start=_mmdd(ws.period_start), end=_mmdd(ws.period_end)
    )
    sections = [
        f"{title1}\n" + section1_unfit.render(report.section1_items, names, cfg["empty_section1"]),
        f"{t[1]}\n" + section2_law.render(report.section2_items, cfg["empty_section2"], reannounce),
        f"{t[2]}\n{section3_tip.render(tip, cfg['empty_section3'])}",
    ]
    checks = [
        section1_unfit.check_lines(
            report.section1_items, names, section1_unfit.pick_review(ws.items)
        ),
        section2_law.check_lines(report.section2_items, period, reannounce, _board_law(ws), names),
        section3_tip.check_lines(tip),
    ]
    text = "\n\n".join(sections)
    check = _check_text(cfg, checks)
    repo.save_report(
        run_id,
        {
            **report.model_dump(mode="json"),
            "tip": tip,
            "reannounce": reannounce,
            "text": text,
            "check": check,
        },
    )
    out = ReportOut(
        report=report, text=text, review_needed=review, customer_names=names, check=check
    )
    return out, ws


def set_tip(run_id: int, tip: str | None) -> None:
    saved = repo.get_report(run_id) or {}
    saved["tip"] = tip or None
    repo.save_report(run_id, saved)


def set_reannounce(run_id: int, text: str | None) -> None:
    """새 개정이 없는 주에 섹션 2에 넣을 재안내 글 (담당자가 근거와 함께 직접 쓴다)."""
    saved = repo.get_report(run_id) or {}
    saved["reannounce"] = text or None
    repo.save_report(run_id, saved)
