"""섹션 2 법령 개정 요약 (DESIGN.md 10-1, RULES.md 11-3).

- 항목마다: 법령·고시명, 구분, 번호, 공포·고시일, 시행일, 주요 개정 조항, 개정 요지,
  관련 식품유형, 출처.
- 법령명·번호·날짜·조항은 입력(b1, 원문) 값만 쓰고, 빈 칸은 "확인 필요".
- 개정 요지는 담당자 수정본(final_summary)이 있으면 그것을, 없으면 AI 요약을 쓴다.
- b1이 "새로 시행된 개정, 이미 보고한 것 제외"로 거른 목록은 본문에 모두 넣는다(누락 방지).
  사람이 봐야 하는 건 빼지 않고 담당자 확인용(check_lines, 보고서 맨 끝)에 함께 적는다.
- 새 개정이 없는 주: "해당 없음" 문장. 담당자가 재안내 글을 저장했으면 그 글을 넣는다.
- 게시판 법령 소식: 선별에서 '법령 개정'(관련·검토 필요)으로 분류됐지만 법령 개정 목록에
  같은 법령명이 없는 글은 빠지지 않게 화면 전용 확인 목록에 보여 준다(메일 글에는 넣지 않음).
- 문구는 config/b2/report.json의 "section2"에만 둔다.
"""

import re
from datetime import date, timedelta
from typing import Any

from app.core.schema import Crosscheck, Label, LawChange, SelectedItem

LAW_NAME = re.compile(r"「([^」]+)」")
LABEL_KO = {Label.relevant: "관련", Label.review_needed: "검토 필요", Label.irrelevant: "무관"}

MISSING = "확인 필요"
MISMATCH = {Crosscheck.api_only, Crosscheck.notice_only}


def _v(x: object) -> str:
    return str(x) if x not in (None, "") else MISSING


def _text() -> dict[str, Any]:
    from app.b2_mail.report.service import config  # service가 이 모듈을 import하므로 늦게 부른다

    data: dict[str, Any] = config()["section2"]
    return data


def summary_of(c: LawChange) -> str | None:
    return c.final_summary or c.ai_summary


def line(c: LawChange) -> str:
    foods = ", ".join(c.related_food_types) or MISSING
    return (
        f"   - 「{_v(c.law_name)}」 {_v(c.change_type)} ({_v(c.number)})\n"
        f"     공포·고시 {_v(c.promulgated_at)} · 시행 {_v(c.effective_at)}\n"
        f"     주요 개정 조항: {_v(c.articles)}\n"
        f"     주요 내용: {_v(summary_of(c))}\n"
        f"     관련 식품유형: {foods}\n"
        f"     출처: {_v(c.source_url)}"
    )


def _short(c: LawChange) -> str:
    return f"   - 「{_v(c.law_name)}」 ({_v(c.number)}) · 시행 {_v(c.effective_at)}"


def _out_of_window(c: LawChange, period: tuple[date, date], lookback: int) -> bool:
    """시행일이 없거나, 보고 기간(월요일 - lookback일 ~ 일요일) 밖이면 True (시행 예정 포함)."""
    if c.effective_at is None:
        return True
    start, end = period
    return not (start - timedelta(days=lookback) <= c.effective_at <= end)


def _group(title: str, lines: list[str]) -> list[str]:
    return [f"  ■ {title} ({len(lines)}건)", *lines] if lines else []


def _norm(name: str) -> str:
    return re.sub(r"\s+", "", name)


def board_only(changes: list[LawChange], board: list[SelectedItem]) -> list[SelectedItem]:
    """게시판 법령 소식 중 법령 개정 목록에 같은 법령명(「…」)이 없는 글. 이름이 없으면 남긴다."""
    known = {_norm(c.law_name) for c in changes if c.law_name}
    out = []
    for i in board:
        m = LAW_NAME.search(i.raw.title or "")
        if not (m and _norm(m.group(1)) in known):
            out.append(i)
    return out


def _board_line(item: SelectedItem, names: dict[str, str]) -> str:
    label = item.selection.final_label or item.selection.ai_label
    cands = [
        names.get(m.customer_id, m.customer_id)
        for m in item.matches
        if (m.final_matched if m.final_matched is not None else m.ai_matched)
    ]
    return (
        f"   - [{_v(item.raw.posted_at)}] {item.raw.title or MISSING}"
        f" / 선별: {LABEL_KO.get(label, label)} / 관련 고객사 후보: {', '.join(cands) or '없음'}"
        f"\n     출처: {_v(item.raw.url)}"
    )


def check_lines(
    changes: list[LawChange],
    period: tuple[date, date],
    reannounce: str | None,
    board: list[SelectedItem] | None = None,
    names: dict[str, str] | None = None,
) -> list[str]:
    """화면 전용 확인 목록: 게시판 법령 소식, 요약 미확인, 대조 불일치, 기간 밖, 재안내 안내."""
    t = _text()
    out: list[str] = []
    extra = board_only(changes, board or [])
    out += _group(t["check_board"], [_board_line(i, names or {}) for i in extra])
    out += _group(t["check_unconfirmed"], [_short(c) for c in changes if not c.final_summary])
    out += _group(t["check_mismatch"], [_short(c) for c in changes if c.crosscheck in MISMATCH])
    out += _group(
        t["check_window"],
        [_short(c) for c in changes if _out_of_window(c, period, int(t["lookback_days"]))],
    )
    if not changes and not reannounce:
        out.append(f"  ■ {t['check_reannounce_hint']}")
    if changes and reannounce:
        out.append(f"  ■ {t['check_reannounce_unused']}")
    return out


def render(changes: list[LawChange], empty: str, reannounce: str | None = None) -> str:
    """본문만 만든다 (담당자용·고객사 메일 공통). 확인용 목록은 check_lines()."""
    t = _text()
    if changes:
        body = [line(c) for c in changes]
    elif reannounce:
        body = [f"   {t['reannounce_intro']}", *(f"   {ln}" for ln in reannounce.splitlines())]
    else:
        body = [f"   {empty}"]
    return "\n".join(body)
