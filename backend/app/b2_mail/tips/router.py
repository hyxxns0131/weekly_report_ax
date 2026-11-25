"""B2-07 오늘의 팁 엔드포인트 (P2)."""

from fastapi import APIRouter
from pydantic import BaseModel

from app.b2_mail.report.service import set_tip
from app.b2_mail.tips.topics import TOPICS, Topic
from app.b2_mail.tips.writer import draft

router = APIRouter()


class TopicOut(Topic):
    draft: str


class TipBody(BaseModel):
    tip: str | None = None


@router.get("/tips/topics", response_model=list[TopicOut])
def topics() -> list[TopicOut]:
    return [TopicOut(**t.model_dump(), draft=draft(t)) for t in TOPICS]


@router.put("/runs/{run_id}/tip", response_model=TipBody)
def put_tip(run_id: int, body: TipBody) -> TipBody:
    set_tip(run_id, body.tip)
    return body
