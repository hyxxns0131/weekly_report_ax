"""B2-04 수정 이력."""

from typing import Any

from app.core.storage import repo


def add(draft_id: int, user: str, body: str) -> None:
    repo.add_history(draft_id, user, body)


def list_for(draft_id: int) -> list[dict[str, Any]]:
    return repo.list_history(draft_id)
