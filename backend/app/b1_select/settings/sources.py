"""B1-15 출처 설정 읽기·저장 (config/b1/sources.json)."""

import json
from typing import Any

from pydantic import BaseModel

from app.core.config import REPO_ROOT

SOURCES_JSON = REPO_ROOT / "backend" / "config" / "b1" / "sources.json"


class SourceSetting(BaseModel):
    id: str
    name: str
    enabled: bool
    mode: str  # auto | manual
    section: int
    allowed: str  # 이용약관·자동 수집 확인 여부


def _read() -> dict[str, Any]:
    data: dict[str, Any] = json.loads(SOURCES_JSON.read_text(encoding="utf-8"))
    return data


def load() -> list[SourceSetting]:
    return [SourceSetting.model_validate(s) for s in _read()["sources"]]


def save(items: list[SourceSetting]) -> list[SourceSetting]:
    data = _read()
    data["sources"] = [s.model_dump() for s in items]
    SOURCES_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return items
