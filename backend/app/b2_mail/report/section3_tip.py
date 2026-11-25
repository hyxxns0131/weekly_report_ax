"""섹션 3 오늘의 팁 (B2-07, RULES.md 12장). 근거 없는 팁은 넣지 않는다.

- 근거 있음 = "근거:" 또는 "출처:"로 시작하는 줄 + 링크(http…)가 팁 글 안에 모두 있음.
- 근거가 없으면 본문은 "해당 없음", 담당자 확인용(발송 전 삭제)에 이유를 적는다.
- "최신본 확인 필요"가 남아 있으면 넣되 담당자 확인용에 알린다.
- 문구는 config/b2/report.json의 "section3"에만 둔다.
"""

import re
from typing import Any

LINK = re.compile(r"https?://\S+")


def _text() -> dict[str, Any]:
    from app.b2_mail.report.service import config  # service가 이 모듈을 import하므로 늦게 부른다

    data: dict[str, Any] = config()["section3"]
    return data


def has_basis(tip: str | None) -> bool:
    """팁에 근거 줄("근거:"/"출처:")과 링크가 모두 있는지."""
    if not tip:
        return False
    markers = tuple(_text()["basis_markers"])
    has_line = any(ln.strip().startswith(markers) for ln in tip.splitlines())
    return has_line and LINK.search(tip) is not None


def _body(tip: str) -> list[str]:
    lines = [ln.rstrip() for ln in tip.strip().splitlines() if ln.strip()]
    return [f"   - {lines[0].strip()}", *(f"     {ln.strip()}" for ln in lines[1:])]


def render(tip: str | None, empty: str, staff: bool = False) -> str:
    """staff=True: 담당자용(확인용 칸 포함). False: 고객사 메일처럼 본문만."""
    t = _text()
    ok = has_basis(tip)
    body = [f"   {t['intro']}", *_body(tip)] if tip and ok else [f"   {empty}"]
    if not staff:
        return "\n".join(body)
    check: list[str] = []
    if not tip:
        check.append(f"  ■ {t['check_no_tip']}")
    elif not ok:
        check.append(f"  ■ {t['check_no_basis']}")
    elif t["latest_marker"] in tip:
        check.append(f"  ■ {t['check_latest']}")
    if check:
        body += ["", f"  {t['check_title']}", *check]
    return "\n".join(body)
