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


def find_food_types(text: str | None) -> list[str]:
    """본문에 나온 식품유형 단어(표준 이름)를 순서대로. 법령·정책 항목의 고객사 후보용.

    찾는 단어는 food_types.json의 words·aliases. 긴 단어부터 보고 찾은 자리는 지워서
    "쌀과자"가 "과자"로 한 번만 잡히게 한다.
    """
    if not text:
        return []
    cfg = _config()
    aliases: dict[str, str] = cfg.get("aliases", {})
    terms = set(cfg.get("words", [])) | set(aliases) | set(aliases.values())
    found: list[tuple[int, str]] = []
    rest = text
    for term in sorted(terms, key=len, reverse=True):
        pos = rest.find(term)
        while pos != -1:
            found.append((pos, aliases.get(term, term)))
            rest = rest[:pos] + " " * len(term) + rest[pos + len(term) :]
            pos = rest.find(term)
    out: list[str] = []
    for _, name in sorted(found):
        if name not in out:
            out.append(name)
    return out
