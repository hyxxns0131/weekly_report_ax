"""B1-01 수동 업로드: CSV·텍스트 붙여넣기·URL → 원문 항목(RawItem).

- CSV: 첫 줄이 열 이름. 한 줄 = 항목 하나. 본문은 "열 이름: 값" 줄로 저장해 추출(B1-09)이 읽는다.
- 텍스트: 빈 줄로 나눈 덩어리 하나 = 항목 하나. 첫 줄이 제목.
- URL: 링크를 원문 항목으로 남긴다(본문은 담당자가 붙여 넣거나 출처 수집기가 채운다).
- 엑셀(.xlsx)은 openpyxl이 필요하다(추가 승인 대기). 그 전에는 엑셀에서 CSV로 저장해 올린다.
"""

import csv
import io
from datetime import date

from app.b1_select.collect.base import CollectResult, make_id
from app.core.schema import RawItem, Source
from app.core.storage.local_db import now_kst

DATE_COLUMNS = ("부적합일자", "게시일", "등록일", "일자", "date")
TITLE_COLUMNS = ("제품명", "제목", "title")
URL_COLUMNS = ("링크", "URL", "url")


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    v = value.strip().replace(".", "-").replace("/", "-")[:10]
    try:
        return date.fromisoformat(v)
    except ValueError:
        return None


def _pick(row: dict[str, str], names: tuple[str, ...]) -> str | None:
    return next((row[n].strip() for n in names if row.get(n) and row[n].strip()), None)


def from_csv(run_id: int, source: Source, text: str) -> CollectResult:
    reader = csv.DictReader(io.StringIO(text.lstrip("﻿")))
    items: list[RawItem] = []
    for row in reader:
        row = {(k or "").strip(): (v or "") for k, v in row.items()}
        body = "\n".join(f"{k}: {v.strip()}" for k, v in row.items() if k and v.strip())
        if not body:
            continue
        items.append(
            RawItem(
                id=make_id(source.value, body),
                run_id=run_id,
                source=source,
                title=_pick(row, TITLE_COLUMNS) or body.splitlines()[0][:80],
                body=body,
                posted_at=_parse_date(_pick(row, DATE_COLUMNS)),
                url=_pick(row, URL_COLUMNS),
                collected_at=now_kst(),
            )
        )
    return CollectResult(
        source=source.value, status="ok", items=items, message=f"CSV {len(items)}건"
    )


def from_text(run_id: int, source: Source, text: str, url: str | None) -> CollectResult:
    blocks = [b.strip() for b in text.replace("\r\n", "\n").split("\n\n") if b.strip()]
    items = [
        RawItem(
            id=make_id(source.value, b),
            run_id=run_id,
            source=source,
            title=b.splitlines()[0][:120],
            body=b,
            url=url,
            collected_at=now_kst(),
        )
        for b in blocks
    ]
    if not items and url:
        items = [
            RawItem(
                id=make_id(source.value, url),
                run_id=run_id,
                source=source,
                title=url,
                body="",
                url=url,
                collected_at=now_kst(),
            )
        ]
    return CollectResult(
        source=source.value, status="ok", items=items, message=f"텍스트 {len(items)}건"
    )
