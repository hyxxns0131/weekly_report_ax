"""수집기 공통 형식 (B1-01~07). 출처 1개 = 파일 1개, 각 수집기는 CollectResult를 돌려준다.

한 출처가 실패해도 다른 출처는 계속한다. 실패하면 status="failed"와 이유를 남기고
화면에 "수집 실패 → 수동 업로드"로 보인다 (RULES.md 6장).
"""

import hashlib

from pydantic import BaseModel, Field

from app.core.schema import RawItem


class CollectResult(BaseModel):
    source: str
    status: str  # ok | failed | manual | off
    items: list[RawItem] = Field(default_factory=list)
    message: str = ""


def make_id(source: str, *parts: str) -> str:
    digest = hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()[:12]
    return f"{source}:{digest}"
