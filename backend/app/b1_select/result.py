"""b2용 WeeklySelection 내보내기: GET /api/b1/runs/{run_id}/result (AGENTS.md 5-6, LSH).

선별·추출·고객사 판단 결과 + 법령 개정 목록. b2는 이 응답만 쓴다.
"""

from fastapi import APIRouter, HTTPException

from app.core.schema import SelectedItem, WeeklySelection
from app.core.storage import local_db, repo

router = APIRouter()


def build(run_id: int) -> WeeklySelection:
    run = local_db.get_run(run_id)
    if run is None:
        raise KeyError(run_id)
    matches = repo.list_matches(run_id)
    items = []
    for raw in repo.list_raw(run_id):
        sel = repo.get_selection(raw.id)
        if sel is None:
            continue
        items.append(
            SelectedItem(
                raw=raw,
                selection=sel,
                extracted=repo.get_extracted(raw.id),
                matches=[m for m in matches if m.item_id == raw.id],
            )
        )
    return WeeklySelection(
        run_id=run_id,
        period_start=run.period_start,
        period_end=run.period_end,
        week_label=run.week_label,
        items=items,
        law_changes=repo.list_law(run_id),
    )


@router.get("/runs/{run_id}/result", response_model=WeeklySelection)
def get_result(run_id: int) -> WeeklySelection:
    try:
        return build(run_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail="주간 실행을 찾을 수 없습니다.") from e
