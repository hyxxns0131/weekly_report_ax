"""수집기 공통 형식 (B1-01~07). 출처 1개 = 파일 1개, 각 수집기는 CollectResult를 돌려준다.

한 출처가 실패해도 다른 출처는 계속한다. 실패하면 status="failed"와 이유를 남기고
화면에 "수집 실패 → 수동 업로드"로 보인다 (RULES.md 6장).

모드 (sources.json의 mode):
- api: 공식 Open API (api_client.py). .env(또는 sources.json api.service)에 설정이
  없으면 수동 업로드로 남긴다.
- demo: 늘 더미. samples/b1_input/demo/<출처id>.json에 저장해 둔 응답을 읽는다.
- manual: 수동 업로드만.
화면 읽기(크롤링)는 하지 않는다.

API·더미 모두 같은 행 형식(Row)을 rows_to_result()로 RawItem으로 바꾼다.
그래서 저장(로컬 DB·서버 DB)·업데이트 날짜·선별·고객사 판단이 같은 길로 이어진다.

행 형식 (demo JSON 한 칸 = api_client.to_row가 돌려주는 dict 하나):
    {"title": "제목(필수)", "posted_at": "YYYY-MM-DD", "url": "원문 링크",
     "body": "본문 글", "fields": {"열 이름": "값", ...}, "key": "원문 고유번호(있으면)"}
"""

import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from app.b1_select.extract.table_mapper import split_tag
from app.core.config import REPO_ROOT
from app.core.schema import RawItem, Source
from app.core.storage.local_db import now_kst

DEMO_DIR = REPO_ROOT / "samples" / "b1_input" / "demo"


class CollectResult(BaseModel):
    source: str
    status: str  # ok | failed | manual | off
    items: list[RawItem] = Field(default_factory=list)
    message: str = ""


def make_id(source: str, *parts: str) -> str:
    digest = hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()[:12]
    return f"{source}:{digest}"


def demo_path(cfg: dict[str, Any]) -> Path:
    """sources.json의 demo_file(저장소 기준 경로). 없으면 samples/b1_input/demo/<id>.json."""
    raw = cfg.get("demo_file")
    if not raw:
        return DEMO_DIR / f"{cfg['id']}.json"
    p = Path(raw)
    return p if p.is_absolute() else REPO_ROOT / p


def _parse_date(value: Any) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(str(value).strip().replace(".", "-").replace("/", "-")[:10])
    except ValueError:
        return None


def _body(row: dict[str, Any]) -> str:
    """fields(열 이름: 값)가 있으면 줄로 펴고, body 글을 뒤에 붙인다. 원문 값은 그대로 둔다.

    "[가공식품] 냉동새우살" 같은 분류 꼬리표는 식품유형·품목 칸에서만 읽는다.
    위반내역의 "[기준: 불검출]" 같은 괄호는 분류가 아니다.
    """
    lines: list[str] = []
    fields: dict[str, Any] = row.get("fields") or {}
    tags: list[str] = []
    for k, v in fields.items():
        if v is None or str(v).strip() == "":
            continue
        lines.append(f"{k}: {str(v).strip()}")
        if "유형" not in k and "품목" not in k:
            continue
        _, tag = split_tag(str(v))
        if tag and tag not in tags:
            tags.append(tag)
    lines += [f"분류: {t}" for t in tags]
    text = str(row.get("body") or "").strip()
    if text:
        lines.append(text)
    return "\n".join(lines)


def load_demo(source_id: str, path: Path, run_id: int, start: date, end: date) -> CollectResult:
    """저장해 둔 응답(JSON 배열) → RawItem 목록. 보고 기간 밖은 버리고, 같은 id는 한 번만."""
    try:
        rows = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return CollectResult(
            source=source_id, status="failed", message=f"데모 파일 없음: {path.name}"
        )
    except (OSError, ValueError) as e:
        return CollectResult(source=source_id, status="failed", message=f"데모 파일 읽기 실패: {e}")
    if not isinstance(rows, list):
        return CollectResult(
            source=source_id, status="failed", message="데모 파일 형식 오류: JSON 배열이 아님"
        )
    return rows_to_result(source_id, rows, run_id, start, end, label="데모")


def rows_to_result(
    source_id: str,
    rows: list[dict[str, Any]],
    run_id: int,
    start: date,
    end: date,
    label: str,
) -> CollectResult:
    """행 목록 → RawItem 목록 (demo·auto 공용). 보고 기간 밖은 버리고, 같은 id는 한 번만."""
    items: list[RawItem] = []
    seen: set[str] = set()
    skipped = 0
    try:
        for row in rows:
            title = str(row["title"]).strip()
            posted = _parse_date(row.get("posted_at"))
            if posted and not (start <= posted <= end):
                skipped += 1
                continue
            key = row.get("key")  # 사이트 고유번호가 있으면 그것으로 id를 만든다
            item_id = (
                f"{source_id}:{key}"
                if key
                else make_id(source_id, title, posted.isoformat() if posted else "")
            )
            if item_id in seen:
                continue
            seen.add(item_id)
            items.append(
                RawItem(
                    id=item_id,
                    run_id=run_id,
                    source=Source(source_id),
                    title=title,
                    body=_body(row),
                    posted_at=posted,
                    url=row.get("url"),
                    collected_at=now_kst(),
                )
            )
    except (KeyError, TypeError, ValueError) as e:
        return CollectResult(source=source_id, status="failed", message=f"{label} 형식 오류: {e}")

    if not items and skipped:
        return CollectResult(
            source=source_id,
            status="ok",
            message=f"{label} 0건 (보고 기간에 새 글 없음 · 기간 밖 {skipped}건)",
        )
    if not items:
        return CollectResult(source=source_id, status="ok", message="0건(구조 변경 의심)")
    note = f" · 기간 밖 {skipped}건 제외" if skipped else ""
    return CollectResult(
        source=source_id, status="ok", items=items, message=f"{label} {len(items)}건{note}"
    )
