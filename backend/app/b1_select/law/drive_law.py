"""B1-12 구글 드라이브 법령 폴더(DRIVE_LAW_FOLDER_ID) → LawChange.

- 구글 시트·CSV: 첫 줄을 칸 이름으로 보고 행마다 LawChange 1개 (칸 이름은 COLUMNS 별칭).
- 구글 문서·txt: 파일 1개 = LawChange 1개. 법령명은 파일 이름, "시행일" 표기가 있으면 그 날짜.
- 그 밖의 파일(PDF·hwp·엑셀 등)은 읽지 않고 건너뛴 개수만 알린다.
- 값은 드라이브 원문에서만 채우고, 없으면 None("확인 필요").
  시행일이 없으면 new_in_force에서 빠진다.
"""

import csv
import hashlib
import io
import re
from datetime import date
from pathlib import Path

from pydantic import BaseModel, Field

from app.b1_select.law import summarize
from app.core.schema import Crosscheck, LawChange
from app.core.storage import drive

TABLE_TYPES = {drive.SHEET, "text/csv"}
TEXT_TYPES = {drive.DOC, "text/plain"}

# LawChange 칸 → 드라이브 표에서 쓸 수 있는 칸 이름 (공백 무시, 앞에 있을수록 우선)
COLUMNS: dict[str, list[str]] = {
    "serial": ["행정규칙일련번호", "일련번호"],
    "law_name": ["법령명", "고시명", "행정규칙명", "법령·고시명", "법령/고시명", "제목"],
    "kind": ["구분", "종류", "법령종류"],
    "change_type": ["제개정구분", "개정구분", "제개정", "제·개정구분"],
    "number": ["고시번호", "발령번호", "공포번호", "번호"],
    "promulgated_at": ["공포일", "고시일", "발령일", "발령일자", "공포일자", "고시일자"],
    "effective_at": ["시행일", "시행일자"],
    "articles": ["주요개정조항", "개정조항", "조항", "조문"],
    "reason": ["개정이유", "제개정이유", "개정요지", "요지", "주요내용"],
    "url": ["출처", "링크", "url", "원문", "원문링크"],
}

DATE_RE = re.compile(r"(\d{4})\s*[.\-/년]\s*(\d{1,2})\s*[.\-/월]\s*(\d{1,2})")
EFFECTIVE_RE = re.compile(
    r"시행\s*(?:일|일자)?\s*[:：]?\s*(\d{4}\s*[.\-/년]\s*\d{1,2}\s*[.\-/월]\s*\d{1,2})"
)


class DriveLawResult(BaseModel):
    changes: list[LawChange] = Field(default_factory=list)
    files: int = 0
    skipped: list[str] = Field(default_factory=list)  # 읽지 않은 파일 경로


def parse_date(v: str | None) -> date | None:
    if not v:
        return None
    s = v.strip()
    if len(s) == 8 and s.isdigit():
        s = f"{s[:4]}.{s[4:6]}.{s[6:]}"
    m = DATE_RE.search(s)
    if not m:
        return None
    try:
        return date(int(m[1]), int(m[2]), int(m[3]))
    except ValueError:
        return None


def _decode(data: bytes) -> str:
    for enc in ("utf-8-sig", "cp949"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def _key(name: str) -> str:
    return re.sub(r"\s+", "", name).lower()


def _column_map(header: list[str]) -> dict[str, int]:
    keys = [_key(h) for h in header]
    out: dict[str, int] = {}
    for field, aliases in COLUMNS.items():
        for a in aliases:
            if _key(a) in keys:
                out[field] = keys.index(_key(a))
                break
    return out


def _id(serial: str | None, *parts: str | None) -> str:
    if serial:
        return f"law:{serial}"  # 법제처 API 항목과 같은 ID → 중복 제거
    raw = "|".join(p or "" for p in parts)
    return f"drive:{hashlib.sha1(raw.encode('utf-8')).hexdigest()[:12]}"


def _clean(v: str | None) -> str | None:
    t = (v or "").strip()
    return t or None


def from_table(text: str, f: drive.DriveFile) -> list[LawChange]:
    rows = list(csv.reader(io.StringIO(text)))
    if not rows:
        return []
    cols = _column_map(rows[0])
    if "law_name" not in cols:
        return []

    out: list[LawChange] = []
    for row in rows[1:]:

        def cell(field: str, row: list[str] = row) -> str | None:
            i = cols.get(field)
            return _clean(row[i]) if i is not None and i < len(row) else None

        name = cell("law_name")
        if not name:
            continue
        number, eff = cell("number"), cell("effective_at")
        out.append(
            LawChange(
                id=_id(cell("serial"), name, number, eff),
                law_name=name,
                kind=cell("kind"),
                change_type=cell("change_type"),
                number=number,
                promulgated_at=parse_date(cell("promulgated_at")),
                effective_at=parse_date(eff),
                articles=cell("articles"),
                ai_summary=summarize.summarize(cell("reason")),
                source_url=cell("url") or f.web_view_link,
                crosscheck=Crosscheck.not_checked,
            )
        )
    return out


def from_text(text: str, f: drive.DriveFile) -> LawChange:
    m = EFFECTIVE_RE.search(text)
    eff = parse_date(m[1]) if m else None
    name = Path(f.name).stem if f.mime_type == "text/plain" else f.name
    return LawChange(
        id=_id(None, f.id),
        law_name=name,
        effective_at=eff,
        ai_summary=summarize.summarize(text),
        source_url=f.web_view_link,
        crosscheck=Crosscheck.not_checked,
    )


def fetch(folder_id: str) -> DriveLawResult:
    """폴더 전체를 읽는다. 바뀐 파일만 새로 받는다(drive.fetch_bytes 캐시)."""
    result = DriveLawResult()
    for f in drive.list_folder(folder_id):
        is_csv = f.mime_type in TABLE_TYPES or f.name.lower().endswith(".csv")
        is_txt = f.mime_type in TEXT_TYPES
        if not (is_csv or is_txt):
            result.skipped.append(f.path)
            continue
        result.files += 1
        text = _decode(drive.fetch_bytes(f))
        if is_csv:
            result.changes.extend(from_table(text, f))
        else:
            result.changes.append(from_text(text, f))
    return result
