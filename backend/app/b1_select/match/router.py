"""B1-11 관련 고객사 판단 엔드포인트."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.b1_select.match.customers import names
from app.core.schema import Confidence, CustomerMatch, MatchRule
from app.core.storage import repo

router = APIRouter()


class MatchRow(CustomerMatch):
    customer_name: str
    item_title: str
    item_url: str | None


class MatchPatch(BaseModel):
    final_matched: bool


@router.get("/runs/{run_id}/matches", response_model=list[MatchRow])
def list_matches(run_id: int) -> list[MatchRow]:
    n = names()
    raws = {r.id: r for r in repo.list_raw(run_id)}
    return [
        MatchRow(
            **m.model_dump(),
            customer_name=n.get(m.customer_id, m.customer_id),
            item_title=raws[m.item_id].title if m.item_id in raws else m.item_id,
            item_url=raws[m.item_id].url if m.item_id in raws else None,
        )
        for m in repo.list_matches(run_id)
    ]


@router.patch("/matches/{item_id}/{customer_id}", response_model=CustomerMatch)
def patch_match(item_id: str, customer_id: str, body: MatchPatch) -> CustomerMatch:
    if repo.get_raw(item_id) is None:
        raise HTTPException(status_code=404, detail="항목을 찾을 수 없습니다.")
    existing = {m.customer_id: m for m in repo.list_matches_for_item(item_id)}
    m = existing.get(customer_id) or CustomerMatch(
        item_id=item_id,
        customer_id=customer_id,
        ai_matched=False,
        rule=MatchRule.food_type_only,
        confidence=Confidence.medium,
        reason="담당자가 직접 추가",
    )
    m.final_matched = body.final_matched
    repo.save_match(m)
    return m
