"""B1-10 국가명 정규화 (목업: config/b1/countries.json)."""

import json
from functools import lru_cache

from app.core.config import REPO_ROOT

CONFIG = REPO_ROOT / "backend" / "config" / "b1" / "countries.json"


@lru_cache
def _aliases() -> dict[str, str]:
    data: dict[str, dict[str, str]] = json.loads(CONFIG.read_text(encoding="utf-8"))
    return data.get("aliases", {})


def normalize_country(raw: str | None) -> str | None:
    if not raw:
        return None
    value = raw.strip()
    return _aliases().get(value, value)
