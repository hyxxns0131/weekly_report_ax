"""B1-13 LawChange 만들기·요약.

법령명·번호·날짜·조항은 API 원문에서만 채우고 없으면 None("확인 필요").
요지는 지금 LLM 없이 제개정 이유 원문을 발췌한다(LLM 요약은 core/llm.py 준비 후).
related_food_types는 법령명·조문·제개정 이유에 나온 식품유형 단어(food_type/normalize.py).
"""

from datetime import date
from typing import Any

from app.b1_select.food_type.normalize import find_food_types
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
    link = _text(row.get("행정규칙상세링크"))
    name = _text(row.get("행정규칙명") or info.get("행정규칙명"))
    return LawChange(
        id=f"law:{serial}",
        law_name=name,
        kind="행정규칙",
        change_type=_text(row.get("제개정구분명") or info.get("제개정구분명")),
        number=_text(row.get("발령번호") or info.get("발령번호")),
        promulgated_at=_date(row.get("발령일자") or info.get("발령일자")),
        effective_at=_date(row.get("시행일자") or info.get("시행일자")),
        articles=articles[:2000] if articles else None,
        ai_summary=summarize(reason),
        source_url=_url(link, serial),
        crosscheck=Crosscheck.not_checked,
        related_food_types=find_food_types(" ".join(t for t in (name, articles, reason) if t)),
    )


def _url(link: str | None, serial: str) -> str | None:
    """응답에 절대 링크(행정규칙상세링크)가 있으면 그것을, 없으면 일련번호로 만든 링크."""
    if link and link.startswith("http"):
        return link
    return DETAIL_URL.format(serial=serial) if serial else None


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
        related_food_types=find_food_types(
            " ".join(str(r.get(k) or "") for k in ("law_name", "articles", "reason_text"))
        ),
    )


def summarize(reason: str | None) -> str | None:
    """LLM 연결 전: 원문 발췌(앞 300자). 원문이 없으면 None → "확인 필요"."""
    if not reason:
        return None
    text = " ".join(reason.split())
    return text if len(text) <= 300 else text[:300] + "… (원문 발췌)"
