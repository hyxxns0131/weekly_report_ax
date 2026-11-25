"""B1-12 이미 보고한 개정 기록 (기존 도구 weekly_reported.json 역할 → 로컬 DB reported_law)."""

from app.core.schema import LawChange
from app.core.storage import repo


def reported_ids() -> set[str]:
    return repo.reported_law_ids()


def mark(run_id: int, changes: list[LawChange]) -> None:
    """보고서가 확정되면 b2가 아니라 b1 law API로 기록한다(확정 흐름은 SAMC 확인 후)."""
    for c in changes:
        repo.mark_law_reported(run_id, c)
