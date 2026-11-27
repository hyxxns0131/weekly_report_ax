"""수집한 공개 원문을 서버 DB(Supabase pub_source_item)에도 남기기 (B1-02~06).

- 공식 API에서 가져온 것만 올린다.
  더미(저장해 둔 가상 응답)·수동 업로드는 올리지 않는다.
- 쓰기는 core/storage/public_db.upsert를 쓴다. secret 키(SUPABASE_SERVICE_ROLE_KEY)가 있는
  PM(KHS) PC에서만 실제로 써지고, 없으면 건너뛰고 "로컬에만 저장"으로 남긴다 (AGENTS.md 5-2).
- 공개 원문만 보낸다. 고객사명·매칭 결과·메일 본문은 보내지 않는다 (AGENTS.md 5-1).
- 올리다 실패해도 수집은 실패로 치지 않는다. 로컬 DB에는 이미 저장돼 다음 단계가 이어진다.
"""

from typing import Any

from app.core.schema import RawItem
from app.core.storage import public_db

TABLE = "pub_source_item"
NO_KEY = "서버 DB 쓰기 키 없음 → 로컬 DB에만 저장"


def to_row(item: RawItem) -> dict[str, Any]:
    """RawItem → pub_source_item 한 행 (supabase/migrations/202611250000_public_info_tables.sql)."""
    return {
        "id": item.id,
        "source": item.source.value,
        "title": item.title,
        "body": item.body,
        "posted_at": item.posted_at.isoformat() if item.posted_at else None,
        "url": item.url,
        "collected_at": item.collected_at.isoformat(),
    }


def save(items: list[RawItem]) -> str:
    """서버 DB에 올리고 화면에 보일 한 줄을 돌려준다."""
    if not items:
        return ""
    if not public_db.can_write():
        return NO_KEY
    try:
        n = public_db.upsert(TABLE, [to_row(i) for i in items])
    except Exception as e:  # noqa: BLE001 - 서버 DB 실패가 수집을 멈추지 않게
        return f"서버 DB 저장 실패(로컬 DB에는 저장): {e}"
    return f"서버 DB 저장 {n}건"
