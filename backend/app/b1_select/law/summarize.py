"""B1-13 LawChange 만들기·요약.

법령명·번호·날짜·조항은 API 원문에서만 채우고 없으면 None("확인 필요").
요지는 LLM(core/llm.py)으로 요약하되, LLM이 꺼져 있거나 준비 전이면 제개정 이유 원문을 발췌한다.
"""

from datetime import date
from typing import Any

from app.core.schema import Crosscheck, LawChange

DETAIL_URL = "https://www.law.go.kr/DRF/lawService.do?target=admrul&ID={serial}&type=HTML"


def _date(v: Any) -> date | None:
    s = str(v or "").strip().replace("-", "").replace(".", "")
    if len(s) != 8 or not s.isdigit():
        return None
    return date(int(s[:4]), int(s[4:6]), int(s[6:]))


def _text(v: Any) -> str | None:
    if v is None:
        return None
    if isinstance(v, list):
        v = "\n".join(str(x) for x in v)
    t = str(v).strip()
    return t or None


def from_admrul(row: dict[str, Any], detail: dict[str, Any] | None) -> LawChange:
    serial = str(row.get("행정규칙일련번호") or row.get("행정규칙ID") or "")
    info = (detail or {}).get("행정규칙기본정보", {})
    reason = _text((detail or {}).get("제개정이유내용") or (detail or {}).get("제개정이유"))
    articles = _text((detail or {}).get("조문내용"))
    return LawChange(
        id=f"law:{serial}",
        law_name=_text(row.get("행정규칙명") or info.get("행정규칙명")),
        kind="행정규칙",
        change_type=_text(row.get("제개정구분명") or info.get("제개정구분명")),
        number=_text(row.get("발령번호") or info.get("발령번호")),
        promulgated_at=_date(row.get("발령일자") or info.get("발령일자")),
        effective_at=_date(row.get("시행일자") or info.get("시행일자")),
        articles=articles[:2000] if articles else None,
        ai_summary=summarize(reason),
        source_url=DETAIL_URL.format(serial=serial) if serial else None,
        crosscheck=Crosscheck.not_checked,
    )


def from_public_row(r: dict[str, Any]) -> LawChange:
    """Supabase pub_law_change 행 → LawChange."""
    return LawChange(
        id=str(r["id"]),
        law_name=r.get("law_name"),
        kind=r.get("kind"),
        change_type=r.get("change_type"),
        number=r.get("number"),
        promulgated_at=_date(r.get("promulgated_at")),
        effective_at=_date(r.get("effective_at")),
        articles=r.get("articles"),
        ai_summary=summarize(r.get("reason_text")),
        source_url=r.get("url"),
    )


def summarize(reason: str | None) -> str | None:
    """LLM 연결 전: 원문 발췌(앞 300자). 원문이 없으면 None → "확인 필요"."""
    if not reason:
        return None
    text = " ".join(reason.split())
    return text if len(text) <= 300 else text[:300] + "… (원문 발췌)"
