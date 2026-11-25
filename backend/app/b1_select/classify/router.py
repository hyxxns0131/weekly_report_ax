"""B1-08 선별 수정 엔드포인트."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.b1_select import pipeline
from app.core.auth.deps import require_login
from app.core.schema import Category, Label, Selection
from app.core.storage import local_db, repo

router = APIRouter()


class SelectionPatch(BaseModel):
    final_label: Label | None = None
    final_category: Category | None = None


@router.patch("/items/{item_id}/selection", response_model=Selection)
def patch_selection(
    item_id: str, body: SelectionPatch, user: Annotated[str, Depends(require_login)]
) -> Selection:
    raw = repo.get_raw(item_id)
    sel = repo.get_selection(item_id)
    if raw is None or sel is None:
        raise HTTPException(status_code=404, detail="분석된 항목을 찾을 수 없습니다.")
    if body.final_label is not None:
        sel.final_label = body.final_label
    if body.final_category is not None:
        sel.final_category = body.final_category
    sel.reviewed_by = user
    sel.reviewed_at = local_db.now_kst()
    repo.save_selection(sel)
    pipeline.after_selection(raw.run_id, item_id)  # 아래 단계 다시 실행 (AGENTS.md 5-6)
    return sel
