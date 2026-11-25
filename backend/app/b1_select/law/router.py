"""B1-12~14 법령 개정 엔드포인트."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.b1_select.law import service
from app.core.schema import LawChange
from app.core.storage import repo

router = APIRouter()


class LawPatch(BaseModel):
    final_summary: str | None = None
    related_food_types: list[str] | None = None


@router.post("/runs/{run_id}/law", response_model=service.LawFetchResult)
def fetch_law(run_id: int) -> service.LawFetchResult:
    try:
        return service.fetch(run_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail="주간 실행을 찾을 수 없습니다.") from e


@router.get("/runs/{run_id}/law", response_model=list[LawChange])
def list_law(run_id: int) -> list[LawChange]:
    return repo.list_law(run_id)


@router.patch("/law/{law_id}", response_model=LawChange)
def patch_law(law_id: str, body: LawPatch) -> LawChange:
    found = repo.get_law(law_id)
    if found is None:
        raise HTTPException(status_code=404, detail="법령 개정 항목을 찾을 수 없습니다.")
    run_id, law = found
    if body.final_summary is not None:
        law.final_summary = body.final_summary or None
    if body.related_food_types is not None:
        law.related_food_types = body.related_food_types
    repo.save_law(run_id, law)
    return law
