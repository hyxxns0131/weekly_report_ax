"""수집기 공통 형식 (B1-01~07). 출처 1개 = 파일 1개, 각 수집기는 CollectResult를 돌려준다.

한 출처가 실패해도 다른 출처는 계속한다. 실패하면 status="failed"와 이유를 남기고
화면에 "수집 실패 → 수동 업로드"로 보인다 (RULES.md 6장).

데모 모드(sources.json의 mode="demo"): 실제 사이트 대신 samples/b1_input/demo/<출처id>.json에
저장해 둔 응답을 읽는다. 나중에 mode를 "auto"로 바꾸고 출처 파일의 auto 자리만 채우면 된다.
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
AUTO_NOT_READY = "실제 수집기 준비 전 → 수동 업로드"


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
    """fields(열 이름: 값)가 있으면 줄로 펴고, body 글을 뒤에 붙인다. 원문 값은 그대로 둔다."""
    lines: list[str] = []
    fields: dict[str, Any] = row.get("fields") or {}
    tags: list[str] = []
    for k, v in fields.items():
        if v is None or str(v).strip() == "":
            continue
        lines.append(f"{k}: {str(v).strip()}")
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
            item_id = make_id(source_id, title, posted.isoformat() if posted else "")
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
        return CollectResult(source=source_id, status="failed", message=f"데모 파일 형식 오류: {e}")

    if not items:
        return CollectResult(source=source_id, status="ok", message="0건(구조 변경 의심)")
    note = f" · 기간 밖 {skipped}건 제외" if skipped else ""
    return CollectResult(
        source=source_id, status="ok", items=items, message=f"데모 {len(items)}건{note}"
    )
