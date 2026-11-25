"""분석 순서(분류 → 추출 → 고객사 판단)와 재실행 규칙 (AGENTS.md 5-6, LSH).

- 분석 실행: 모든 원문을 분류하고, 관련·검토 필요만 추출·고객사 판단.
- 선별을 바꾸면: 그 항목의 추출 → 고객사 판단을 다시. 무관이 되면 AI 판단을 지운다.
- 추출 칸을 바꾸면: 그 항목의 고객사 판단만 다시.
- final_*는 어떤 재실행에서도 덮어쓰지 않는다.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.b1_select.classify.service import classify_item
from app.b1_select.extract.service import extract_item
from app.b1_select.match.customers import load_customers
from app.b1_select.match.service import clear_item, match_item
from app.core.schema import Label
from app.core.storage import local_db, repo

router = APIRouter()


class AnalyzeResult(BaseModel):
    total: int
    relevant: int
    review_needed: int
    irrelevant: int
    matches: int


def _effective(item_id: str) -> Label | None:
    sel = repo.get_selection(item_id)
    return (sel.final_label or sel.ai_label) if sel else None


def analyze(run_id: int) -> AnalyzeResult:
    customers = load_customers()
    counts = {Label.relevant: 0, Label.review_needed: 0, Label.irrelevant: 0}
    raws = repo.list_raw(run_id)
    for raw in raws:
        classify_item(raw.id, raw.title, raw.body)
        label = _effective(raw.id) or Label.review_needed
        counts[label] += 1
        if label == Label.irrelevant:
            clear_item(raw.id)
            continue
        extract_item(raw)
        match_item(raw.id, customers)
    return AnalyzeResult(
        total=len(raws),
        relevant=counts[Label.relevant],
        review_needed=counts[Label.review_needed],
        irrelevant=counts[Label.irrelevant],
        matches=len(repo.list_matches(run_id)),
    )


def after_selection(run_id: int, item_id: str) -> None:
    raw = repo.get_raw(item_id)
    if raw is None:
        return
    if _effective(item_id) == Label.irrelevant:
        clear_item(item_id)
        return
    extract_item(raw)
    match_item(item_id)


def after_extracted(run_id: int, item_id: str) -> None:
    match_item(item_id)


@router.post("/runs/{run_id}/analyze", response_model=AnalyzeResult)
def analyze_endpoint(run_id: int) -> AnalyzeResult:
    if local_db.get_run(run_id) is None:
        raise HTTPException(status_code=404, detail="주간 실행을 찾을 수 없습니다.")
    return analyze(run_id)
