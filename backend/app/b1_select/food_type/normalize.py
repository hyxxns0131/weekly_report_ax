"""B1-10 식품유형 표기 정규화 (목업: config/b1/food_types.json의 aliases)."""

import json
from functools import lru_cache
from typing import Any

from app.core.config import REPO_ROOT

CONFIG = REPO_ROOT / "backend" / "config" / "b1" / "food_types.json"


@lru_cache
def _config() -> dict[str, Any]:
    data: dict[str, Any] = json.loads(CONFIG.read_text(encoding="utf-8"))
    return data


def normalize_food_type(raw: str | None) -> str | None:
    if not raw:
        return None
    value = raw.strip()
    aliases: dict[str, str] = _config().get("aliases", {})
    return aliases.get(value, value)
