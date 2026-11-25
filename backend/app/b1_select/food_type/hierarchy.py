"""B1-10 식품유형 상하위 (목업: config/b1/food_types.json의 parents)."""

from app.b1_select.food_type.normalize import _config


def parent_of(food_type: str | None) -> str | None:
    if not food_type:
        return None
    parents: dict[str, str] = _config().get("parents", {})
    return parents.get(food_type)
