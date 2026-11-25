"""B2-06 과거 보고서 정답 읽기: samples/past_reports/*.json (비식별, KHW).

형식(제안): {"week": "2026-11 2주차", "items": [{"key": "제품명 또는 제목", "customers": ["C001"]}]}
정답 자료는 SAMC 전달 대기.
"""

import json

from pydantic import BaseModel, Field

from app.core.config import REPO_ROOT

PAST = REPO_ROOT / "samples" / "past_reports"


class GoldenItem(BaseModel):
    key: str
    customers: list[str] = Field(default_factory=list)


class Golden(BaseModel):
    week: str
    items: list[GoldenItem]


def list_weeks() -> list[str]:
    return [load_file(p.name).week for p in sorted(PAST.glob("*.json"))]


def load_file(name: str) -> Golden:
    return Golden.model_validate(json.loads((PAST / name).read_text(encoding="utf-8")))


def find(week: str) -> Golden | None:
    for p in sorted(PAST.glob("*.json")):
        g = load_file(p.name)
        if g.week == week:
            return g
    return None
